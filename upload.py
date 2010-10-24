from sys import stdin, stderr, argv
from csv import DictReader
from ConfigParser import ConfigParser
from json import JSONEncoder, load
from re import compile

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


if __name__ == '__main__':

    cfg = ConfigParser()
    cfg.read(argv[1])
    
    access = cfg.get('aws', 'access')
    secret = cfg.get('aws', 'secret')
    bucket = cfg.get('aws', 'bucket')

    s3 = Bucket(S3Connection(access, secret), bucket)
    
    if len(argv) >= 3:
        print >> stderr, 'GeoJSON...',
        
        geojson = load(open(argv[2], 'r'))
        geometries = dict( [('%(STATE)s%(COUNTY)s%(TRACT)s' % f['properties'], f['geometry']) for f in geojson['features']] )
    
        print >> stderr, '.'
    
    for row in DictReader(stdin, dialect='excel-tab'):
    
        demographics = [
                        (int(row['Population']), 'Population', 'P001001'),
                        (int(row['Housing Units']), 'Housing Units', 'H001001')
                       ]
        
        for (key, name) in values:
            demographics.append( (int(row[key]), name, key) )

        geography = {
                     'Latitude': float(row['Latitude']),
                     'Longitude': float(row['Longitude']),
                     'Land Area': int(row['Land Area']),
                     'Water Area': int(row['Water Area'])
                    }
        
        if row['Summary Level'] == '040':
            #
            # A state
            #
            content = {
                       'Name': row['Name'],
                       'FIPS': row['State FIPS'],
                       'Summary Level': row['Summary Level'],
                       'Geography': geography,
                       'Demographics': demographics
                      }
            
            key = 'states/%(State FIPS)s.json' % row

        elif row['Summary Level'] == '050':
            #
            # A county
            #
            content = {
                       'Name': row['Name'],
                       'FIPS': row['State FIPS'] + row['County FIPS'],
                       'Summary Level': row['Summary Level'],
                       'State': 'http://%s.s3.amazonaws.com/states/%s.json' % (bucket, row['State FIPS']),
                       'Geography': geography,
                       'Demographics': demographics
                      }
            
            key = 'counties/%(State FIPS)s/%(County FIPS)s.json' % row
            
        elif row['Summary Level'] == '080':
            #
            # A tract
            #
            fips = row['State FIPS'] + row['County FIPS'] + row['Tract']
            
            geography['geometry'] = None
            
            for key in (fips, fips[:-2]):
                if key in geometries:
                    geography['geometry'] = geometries[key]
                    break

            content = {
                       'Name': row['Name'],
                       'FIPS': fips,
                       'Summary Level': row['Summary Level'],
                       'State': 'http://%s.s3.amazonaws.com/states/%s.json' % (bucket, row['State FIPS']),
                       'County': 'http://%s.s3.amazonaws.com/counties/%s/%s.json' % (bucket, row['State FIPS'], row['County FIPS']),
                       'Geography': geography,
                       'Demographics': demographics
                      }
            
            key = 'tracts/%(State FIPS)s/%(County FIPS)s/%(Tract)s.json' % row
            
        elif row['Summary Level'] == '080':
            #
            # A zip code
            #
            content = {
                       'Name': row['Name'],
                       'Zip': row['Zip'],
                       'Summary Level': row['Summary Level'],
                       'State': 'http://%s.s3.amazonaws.com/states/%s.json' % (bucket, row['State FIPS']),
                       'Geography': geography,
                       'Demographics': demographics
                      }
            
            key = 'zips/%(State FIPS)s/%(Zip)s.json' % row
            
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
        
        print row['Name']
