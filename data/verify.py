from json import load as jsonload
from urllib import urlopen, urlencode
from httplib import HTTPConnection

def generate_locations():
    """
    """
    # hawaii
    yield 19.6, -155.5
    yield 20.1, -156.4
    yield 20.9, -156.6
    yield 21.5, -158.0
    yield 21.7, -158.8
    yield 22.1, -159.5
    
    # western lower 48
    for lon in range(-124, -73, 2):
        for lat in range(26, 49, 2):
            yield lat, lon
    
    # eastern lower 48
    for lon in range(-74, -65, 1):
        for lat in range(40, 48, 1):
            yield lat, lon
    
    # alaska
    for lon in range(-164, -127, 4):
        for lat in range(52, 69, 4):
            yield lat, lon

if __name__ == '__main__':
    
    tt_host = 'this-tract.s3.amazonaws.com'
    fcc_host, fcc_path = 'data.fcc.gov', '/api/block/2000/find'
    
    for (lat, lon) in generate_locations():
        q = {'format': 'json', 'latitude': lat, 'longitude': lon}
        
        conn = HTTPConnection(fcc_host)
        conn.request('GET', fcc_path + '?' + urlencode(q))
        resp = conn.getresponse()
        data = jsonload(resp)
        
        if resp.status == 500:
            assert data['Err']['msg'] == 'There are no results for this location', data['Err']
            
            print '--'
            continue

        assert resp.status == 200
        assert data['status'] == 'OK'
        
        block = data['Block']['FIPS']
        state, county, tract = block[0:2], block[2:5], block[5:11]
        
        print float(lat), float(lon), state, county, tract
        
        conn = HTTPConnection(tt_host)
        conn.request('GET', '/2000/tracts/%(state)s/%(county)s/%(tract)s.json' % locals())
        resp = conn.getresponse()
        data = jsonload(resp)
        
        assert resp.status == 200
        assert data['FIPS'] == ''.join([state, county, tract])
