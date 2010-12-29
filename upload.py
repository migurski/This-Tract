from sys import stdin, stderr, argv
from csv import DictReader
from ConfigParser import ConfigParser
from json import JSONEncoder, load
from itertools import izip
from re import compile, match
from datetime import datetime

from shapely import wkt
from psycopg2 import connect
from boto.s3.connection import S3Connection
from boto.s3 import Bucket

# Summary Level
# Geographic Component
# State FIPS
# Place FIPS
# County FIPS
# Tract
# Zip
# Block
# Name
# Latitude
# Longitude
# Land Area
# Water Area
# Population
# Housing Units

def log(*bits):
    """
    """
    bits = [str(datetime.now())] + map(str, bits)
    
    f = open('errors.txt', 'a')
    print >> f, '\t'.join(bits)
    f.close()

def summable_field(name):
    return name in ('Population', 'Housing Units', 'Land Area', 'Water Area') or match(r'^P\d{6}$', name)

def generate_areas(sf1_file, sf3_file):
    """
    """
    fips_rows = {}
    
    for (sf1_row, sf3_row) in izip(sf1_file, sf3_file):
    
        keys = 'Summary Level', 'State FIPS', 'County FIPS', 'Tract'
        sf1_id = tuple([sf1_row[key] for key in keys])
        sf3_id = tuple([sf3_row[key] for key in keys])
        
        if sf1_id != sf3_id:
            raise Exception('Mismatched rows')

        if sf1_id in fips_rows:
            fips_rows[sf1_id].append((sf1_row, sf3_row))
        else:
            fips_rows[sf1_id] = [(sf1_row, sf3_row)]

    for fips in sorted(fips_rows.keys()):
        sf1_row, sf3_row = fips_rows[fips][0]
        
        lats, lons = [float(sf1_row['Latitude'])], [float(sf1_row['Longitude'])]
        
        for (sf1_other, sf3_other) in fips_rows[fips][1:]:
            lats.append(float(sf1_other['Latitude']))
            lons.append(float(sf1_other['Longitude']))
            
            for key in sf1_other.keys():
                if summable_field(key):
                    sf1_row[key] = float(sf1_row[key]) + float(sf1_other[key])
            
            for key in sf3_other.keys():
                if summable_field(key):
                    sf3_row[key] = float(sf3_row[key]) + float(sf3_other[key])
        
        sf1_row['Latitude'] = sum(lats) / len(lats)
        sf1_row['Longitude'] = sum(lons) / len(lons)
        
        yield (sf1_row, sf3_row)

def get_simple_geom(db, table_name, column_names, key_values):
    """
    """
    assert len(column_names) == len(key_values)
    
    where_clause = ' AND '.join([col+' = %s' for col in column_names])
    
    q = """SELECT gid,
                  ST_AsText(ST_Envelope(ST_Transform(the_geom, 900913))) AS geom
           FROM %(table_name)s
           WHERE %(where_clause)s
        """ % locals()
    
    try:
        db.execute(q, key_values)
    except Exception, e:
        db.execute('ROLLBACK')
        db.execute('BEGIN')
        log('get_simple_geom query one', str(e).strip(), *key_values)
        return None
    
    gids, bboxes = [], []
    
    for (gid, geom_wkt) in db.fetchall():
        gids.append('%d' % gid)
        bboxes.append(wkt.loads(geom_wkt))
    
    gids = ','.join(gids)
    
    bbox = reduce(lambda a, b: a.union(b), bboxes)
    xmin, ymin, xmax, ymax = bbox.bounds
    span = min(xmax - xmin, ymax - ymin)
    tolerance = span/200
    
    q = """SELECT ST_AsText(ST_Transform(ST_SimplifyPreserveTopology(g, %(tolerance).6f), 4326))
           FROM (
               SELECT ST_Transform(ST_Union(the_geom), 900913) AS g
               FROM %(table_name)s
               WHERE gid IN (%(gids)s)
           ) AS collected
        """ % locals()
    
    try:
        db.execute(q)
        (geom_wkt, ) = db.fetchone()
    except Exception, e:
        db.execute('ROLLBACK')
        db.execute('BEGIN')
        log('get_simple_geom query two', str(e).strip(), *key_values)
        return None
    else:
        return wkt.loads(geom_wkt).__geo_interface__

def get_deg1_neighbors(db, table_name, column_names, key_values):
    """
    """
    assert len(column_names) == len(key_values)
    
    column_list = ', '.join(column_names)
    where_clause = ' AND '.join([col+' = %s' for col in column_names])
    where_not_clause = ' OR '.join([col+' != %s' for col in column_names])
    
    q = """SELECT DISTINCT %(column_list)s
           FROM (
               SELECT ST_Union(the_geom) AS center_geom
               FROM %(table_name)s
               WHERE %(where_clause)s
           ) AS center
           JOIN %(table_name)s
             ON the_geom && center_geom
            AND ST_Intersects(the_geom, center_geom)
           WHERE %(where_not_clause)s
        """ % locals()
    
    try:
        db.execute(q, list(key_values) + list(key_values))
    except Exception, e:
        db.execute('ROLLBACK')
        db.execute('BEGIN')
        log('get_deg1_neighbors', str(e).strip(), *key_values)
        return set()
    else:
        return set(db.fetchall())

def get_deg2_neighbors(db, table_name, column_names, key_values):
    """
    """
    assert len(column_names) == len(key_values)
    
    column_list = ', '.join(column_names)
    where_clause = ' AND '.join([col+' = %s' for col in column_names])
    where_not_clause = ' OR '.join([col+' != %s' for col in column_names])
    
    q = """SELECT DISTINCT %(column_list)s
           FROM (
               SELECT ST_Union(the_geom) AS deg1_geom
               FROM (
                   SELECT ST_Union(the_geom) AS center_geom
                   FROM %(table_name)s
                   WHERE %(where_clause)s
               ) AS center
               JOIN %(table_name)s
                 ON the_geom && center_geom
                AND ST_Intersects(the_geom, center_geom)
           ) AS degree1
           JOIN %(table_name)s
             ON the_geom && deg1_geom
            AND ST_Intersects(the_geom, deg1_geom)
           WHERE %(where_not_clause)s
        """ % locals()
    
    try:
        db.execute(q, list(key_values) + list(key_values))
    except Exception, e:
        db.execute('ROLLBACK')
        db.execute('BEGIN')
        log('get_deg2_neighbors', str(e).strip(), *key_values)
        return set()
    else:
        return set(db.fetchall())

values = [
          # skipped P007001
          # 2-
          ('P007002', 'White alone'),
          ('P007003', 'Black or African American alone'),
          ('P007004', 'American Indian and Alaska Native alone'),
          ('P007005', 'Asian alone'),
          ('P007006', 'Native Hawaiian and Other Pacific Islander alone'),
          ('P007007', 'Some other race alone'),
          ('P007008', 'Two or more races'),
          # skipped P012001
          # 9-
          ('P012002', 'Male'),
          ('P012003', 'Male under 5 years'),
          ('P012004', 'Male 5 to 9 years'),
          ('P012005', 'Male 10 to 14 years'),
          ('P012006', 'Male 15 to 17 years'),
          ('P012007', 'Male 18 and 19 years'),
          ('P012008', 'Male 20 years'),
          # 16-
          ('P012009', 'Male 21 years'),
          ('P012010', 'Male 22 to 24 years'),
          ('P012011', 'Male 25 to 29 years'),
          ('P012012', 'Male 30 to 34 years'),
          ('P012013', 'Male 35 to 39 years'),
          ('P012014', 'Male 40 to 44 years'),
          ('P012015', 'Male 45 to 49 years'),
          ('P012016', 'Male 50 to 54 years'),
          ('P012017', 'Male 55 to 59 years'),
          ('P012018', 'Male 60 and 61 years'),
          ('P012019', 'Male 62 to 64 years'),
          # 27-
          ('P012020', 'Male 65 and 66 years'),
          ('P012021', 'Male 67 to 69 years'),
          ('P012022', 'Male 70 to 74 years'),
          ('P012023', 'Male 75 to 79 years'),
          ('P012024', 'Male 80 to 84 years'),
          ('P012025', 'Male 85 years and over'),
          # 33-
          ('P012026', 'Female'),
          ('P012027', 'Female under 5 years'),
          ('P012028', 'Female 5 to 9 years'),
          ('P012029', 'Female 10 to 14 years'),
          ('P012030', 'Female 15 to 17 years'),
          ('P012031', 'Female 18 and 19 years'),
          ('P012032', 'Female 20 years'),
          # 40-
          ('P012033', 'Female 21 years'),
          ('P012034', 'Female 22 to 24 years'),
          ('P012035', 'Female 25 to 29 years'),
          ('P012036', 'Female 30 to 34 years'),
          ('P012037', 'Female 35 to 39 years'),
          ('P012038', 'Female 40 to 44 years'),
          ('P012039', 'Female 45 to 49 years'),
          ('P012040', 'Female 50 to 54 years'),
          ('P012041', 'Female 55 to 59 years'),
          ('P012042', 'Female 60 and 61 years'),
          ('P012043', 'Female 62 to 64 years'),
          # 51-
          ('P012044', 'Female 65 and 66 years'),
          ('P012045', 'Female 67 to 69 years'),
          ('P012046', 'Female 70 to 74 years'),
          ('P012047', 'Female 75 to 79 years'),
          ('P012048', 'Female 80 to 84 years'),
          ('P012049', 'Female 85 years and over'),
          # skipped P026001
          # 57-
          ('P026002', 'Family households'),
          ('P026003', '2-person family household'),
          ('P026004', '3-person family household'),
          ('P026005', '4-person family household'),
          ('P026006', '5-person family household'),
          ('P026007', '6-person family household'),
          ('P026008', '7-or-more-person family household'),
          # 64-
          ('P026009', 'Nonfamily households:'),
          ('P026010', '1-person nonfamily household'),
          ('P026011', '2-person nonfamily household'),
          ('P026012', '3-person nonfamily household'),
          ('P026013', '4-person nonfamily household'),
          ('P026014', '5-person nonfamily household'),
          ('P026015', '6-person nonfamily household'),
          ('P026016', '7-or-more-person nonfamily household')
         ]

sf3_values = [
          # ?
          ('P007002', 'Not Hispanic'),
          ('P007003', 'Not Hispanic and White alone'),
          ('P007004', 'Not Hispanic and Black or African American alone'),
          ('P007005', 'Not Hispanic and American Indian and Alaska Native alone'),
          ('P007006', 'Not Hispanic and Asian alone'),
          ('P007007', 'Not Hispanic and Native Hawaiian and Other Pacific Islander alone'),
          ('P007008', 'Not Hispanic and Some other race alone'),
          ('P007009', 'Not Hispanic and Two or more races'),
          # ? + 8
          ('P007010', 'Hispanic'),
          ('P007011', 'Hispanic and White alone'),
          ('P007012', 'Hispanic and Black or African American alone'),
          ('P007013', 'Hispanic and American Indian and Alaska Native alone'),
          ('P007014', 'Hispanic and Asian alone'),
          ('P007015', 'Hispanic and Native Hawaiian and Other Pacific Islander alone'),
          ('P007016', 'Hispanic and Some other race alone'),
          ('P007017', 'Hispanic and Two or more races'),
          # ? + 16
          ('P037001', 'Total Age 25+'),
          # ? + 17
          ('P037002', 'Male Age 25+'),
          ('P037003', 'Male Age 25+ No schooling completed'),
          ('P037004', 'Male Age 25+ Nursery to 4th grade'),
          ('P037005', 'Male Age 25+ 5th and 6th grade'),
          ('P037006', 'Male Age 25+ 7th and 8th grade'),
          ('P037007', 'Male Age 25+ 9th grade'),
          ('P037008', 'Male Age 25+ 10th grade'),
          ('P037009', 'Male Age 25+ 11th grade'),
          ('P037010', 'Male Age 25+ 12th grade, no diploma'),
          ('P037011', 'Male Age 25+ High school graduate (includes equivalency)'),
          ('P037012', 'Male Age 25+ Some college, less than 1 year'),
          ('P037013', 'Male Age 25+ Some college, 1 or more years, no degree'),
          ('P037014', 'Male Age 25+ Associate degree'),
          ('P037015', "Male Age 25+ Bachelor's degree"),
          ('P037016', "Male Age 25+ Master's degree"),
          ('P037017', 'Male Age 25+ Professional school degree'),
          ('P037018', 'Male Age 25+ Doctorate degree'),
          # ? + 34
          ('P037019', 'Female Age 25+'),
          ('P037020', 'Female Age 25+ No schooling completed'),
          ('P037021', 'Female Age 25+ Nursery to 4th grade'),
          ('P037022', 'Female Age 25+ 5th and 6th grade'),
          ('P037023', 'Female Age 25+ 7th and 8th grade'),
          ('P037024', 'Female Age 25+ 9th grade'),
          ('P037025', 'Female Age 25+ 10th grade'),
          ('P037026', 'Female Age 25+ 11th grade'),
          ('P037027', 'Female Age 25+ 12th grade, no diploma'),
          ('P037028', 'Female Age 25+ High school graduate (includes equivalency)'),
          ('P037029', 'Female Age 25+ Some college, less than 1 year'),
          ('P037030', 'Female Age 25+ Some college, 1 or more years, no degree'),
          ('P037031', 'Female Age 25+ Associate degree'),
          ('P037032', "Female Age 25+ Bachelor's degree"),
          ('P037033', "Female Age 25+ Master's degree"),
          ('P037034', 'Female Age 25+ Professional school degree'),
          ('P037035', 'Female Age 25+ Doctorate degree'),
          # ? + 51
          ('P052001', 'Households'),
          ('P052002', 'Households Earning Less than $10,000'),
          ('P052003', 'Households Earning $10,000 to $14,999'),
          ('P052004', 'Households Earning $15,000 to $19,999'),
          ('P052005', 'Households Earning $20,000 to $24,999'),
          ('P052006', 'Households Earning $25,000 to $29,999'),
          ('P052007', 'Households Earning $30,000 to $34,999'),
          ('P052008', 'Households Earning $35,000 to $39,999'),
          ('P052009', 'Households Earning $40,000 to $44,999'),
          ('P052010', 'Households Earning $45,000 to $49,999'),
          ('P052011', 'Households Earning $50,000 to $59,999'),
          ('P052012', 'Households Earning $60,000 to $74,999'),
          ('P052013', 'Households Earning $75,000 to $99,999'),
          ('P052014', 'Households Earning $100,000 to $124,999'),
          ('P052015', 'Households Earning $125,000 to $149,999'),
          ('P052016', 'Households Earning $150,000 to $199,999'),
          ('P052017', 'Households Earning $200,000 or more'),
          # ? + 68
          ('P076001', 'Families'),
          ('P076002', 'Families Earning Less than $10,000'),
          ('P076003', 'Families Earning $10,000 to $14,999'),
          ('P076004', 'Families Earning $15,000 to $19,999'),
          ('P076005', 'Families Earning $20,000 to $24,999'),
          ('P076006', 'Families Earning $25,000 to $29,999'),
          ('P076007', 'Families Earning $30,000 to $34,999'),
          ('P076008', 'Families Earning $35,000 to $39,999'),
          ('P076009', 'Families Earning $40,000 to $44,999'),
          ('P076010', 'Families Earning $45,000 to $49,999'),
          ('P076011', 'Families Earning $50,000 to $59,999'),
          ('P076012', 'Families Earning $60,000 to $74,999'),
          ('P076013', 'Families Earning $75,000 to $99,999'),
          ('P076014', 'Families Earning $100,000 to $124,999'),
          ('P076015', 'Families Earning $125,000 to $149,999'),
          ('P076016', 'Families Earning $150,000 to $199,999'),
          ('P076017', 'Families Earning $200,000 or more')
         ]

if __name__ == '__main__':

    config_file, sf1_file, sf3_file = argv[1:]
    
    cfg = ConfigParser()
    cfg.read(config_file)
    
    access = cfg.get('aws', 'access')
    secret = cfg.get('aws', 'secret')
    bucket = cfg.get('aws', 'bucket')

    s3 = Bucket(S3Connection(access, secret), bucket)
    
    hostname = cfg.get('pgsql', 'hostname')
    database = cfg.get('pgsql', 'database')
    username = cfg.get('pgsql', 'username')
    password = cfg.get('pgsql', 'password')
    
    dsn = ' '.join(['%s=%s' % (k, v) for (k, v) in dict(host=hostname, dbname=database, user=username, password=password).items() if v])

    db = connect(dsn).cursor()
    
    files = [DictReader(open(file, 'r'), dialect='excel-tab') for file in (sf1_file, sf3_file)]
    
    for (row, sf3_row) in generate_areas(*files):
    
        demographics = [
                        (int(row['Population']), 'Population', 'P001001'),
                        (int(row['Housing Units']), 'Housing Units', 'H001001')
                       ]
        
        for (key, name) in values:
            demographics.append( (int(row[key]), name, key) )

        for (key, name) in sf3_values:
            demographics.append( (int(sf3_row[key]), name, key) )
        
        geography = {
                     'Latitude': float(row['Latitude']),
                     'Longitude': float(row['Longitude']),
                     'Land Area': int(row['Land Area']),
                     'Water Area': int(row['Water Area'])
                    }
        
        if row['Summary Level'] == '010':
            #
            # Whole country
            #
            geography['geometry'] = None

            content = {
                       'Name': row['Name'],
                       'Summary Level': row['Summary Level'],
                       'Geography': geography,
                       'Demographics': demographics
                      }
            
            key = '2000/country.json'

        elif row['Summary Level'] == '040':
            #
            # A state
            #
            cols, keys = ['state'], [row['State FIPS']]
            geometry = get_simple_geom(db, 'states_2000', cols, keys)
            geography['geometry'] = geometry
            
            deg1_neighbors = get_deg1_neighbors(db, 'states_2000', cols, keys)
            deg2_neighbors = get_deg2_neighbors(db, 'states_2000', cols, keys)
            state_format = 'http://%s.s3.amazonaws.com/2000/states/%s.json'
            neighbors = [
                         [state_format % (bucket, s) for (s, ) in sorted(deg1_neighbors)],
                         [state_format % (bucket, s) for (s, ) in sorted(deg2_neighbors.difference(deg1_neighbors))]
                        ]
            geography['neighbors'] = neighbors

            content = {
                       'Name': row['Name'],
                       'FIPS': row['State FIPS'],
                       'Summary Level': row['Summary Level'],
                       'Geography': geography,
                       'Demographics': demographics
                      }
            
            key = '2000/states/%(State FIPS)s.json' % row

        elif row['Summary Level'] == '050':
            #
            # A county
            #
            cols, keys = ['state', 'county'], [row['State FIPS'], row['County FIPS']]
            geometry = get_simple_geom(db, 'counties_2000', cols, keys)
            geography['geometry'] = geometry
            
            deg1_neighbors = get_deg1_neighbors(db, 'counties_2000', cols, keys)
            deg2_neighbors = get_deg2_neighbors(db, 'counties_2000', cols, keys)
            county_format = 'http://%s.s3.amazonaws.com/2000/counties/%s/%s.json'
            neighbors = [
                         [county_format % (bucket, s, c) for (s, c) in sorted(deg1_neighbors)],
                         [county_format % (bucket, s, c) for (s, c) in sorted(deg2_neighbors.difference(deg1_neighbors))]
                        ]
            geography['neighbors'] = neighbors

            content = {
                       'Name': row['Name'],
                       'FIPS': row['State FIPS'] + row['County FIPS'],
                       'Summary Level': row['Summary Level'],
                       'State': 'http://%s.s3.amazonaws.com/2000/states/%s.json' % (bucket, row['State FIPS']),
                       'Geography': geography,
                       'Demographics': demographics
                      }
            
            key = '2000/counties/%(State FIPS)s/%(County FIPS)s.json' % row
            
        elif row['Summary Level'] == '080':
            #
            # A tract
            #
            cols = 'state', 'county', 'tract'
            
            if row['Tract'].endswith('00'):
                keys = row['State FIPS'], row['County FIPS'], row['Tract'][:4]
            else:
                keys = row['State FIPS'], row['County FIPS'], row['Tract']
            
            geometry = get_simple_geom(db, 'tracts_2000', cols, keys)
            geography['geometry'] = geometry

            deg1_neighbors = get_deg1_neighbors(db, 'tracts_2000', cols, keys)
            deg2_neighbors = get_deg2_neighbors(db, 'tracts_2000', cols, keys)
            tract_format = 'http://%s.s3.amazonaws.com/2000/tracts/%s/%s/%s.json'
            neighbors = [
                         [tract_format % (bucket, s, c, t) for (s, c, t) in sorted(deg1_neighbors)],
                         [tract_format % (bucket, s, c, t) for (s, c, t) in sorted(deg2_neighbors.difference(deg1_neighbors))]
                        ]
            geography['neighbors'] = neighbors

            content = {
                       'Name': row['Name'],
                       'FIPS': row['State FIPS'] + row['County FIPS'] + row['Tract'],
                       'Summary Level': row['Summary Level'],
                       'State': 'http://%s.s3.amazonaws.com/2000/states/%s.json' % (bucket, row['State FIPS']),
                       'County': 'http://%s.s3.amazonaws.com/2000/counties/%s/%s.json' % (bucket, row['State FIPS'], row['County FIPS']),
                       'Geography': geography,
                       'Demographics': demographics
                      }
            
            key = '2000/tracts/%(State FIPS)s/%(County FIPS)s/%(Tract)s.json' % row
            
        elif row['Summary Level'] == '080':
            #
            # A zip code
            #
            content = {
                       'Name': row['Name'],
                       'Zip': row['Zip'],
                       'Summary Level': row['Summary Level'],
                       'State': 'http://%s.s3.amazonaws.com/2000/states/%s.json' % (bucket, row['State FIPS']),
                       'Geography': geography,
                       'Demographics': demographics
                      }
            
            key = '2000/zips/%(State FIPS)s/%(Zip)s.json' % row
            
        else:
            raise Exception('Not sure what to do with summary level "%(Summary Level)s"' % row)
        
        content_arr = []
        float_pat = compile(r'^-?\d+\.\d+$')
        encoded = JSONEncoder(indent=2).iterencode(content)

        for atom in encoded:
            if float_pat.match(atom):
                content_arr.append('%.6f' % float(atom))
            else:
                content_arr.append(atom)
        
        object = s3.new_key(key)
        object.set_contents_from_string(''.join(content_arr), headers={'Content-Type': 'text/json'})
        object.set_canned_acl('public-read')
        
        print key, '--', row['Name']
