function nicenumber(value)
{
    if(value < 10)
    {
        return value.toFixed(1);
    }

    var valueText = value.toFixed(0);
    
    while(valueText.match(/\d{4}\b/))
    {
        valueText = valueText.replace(/^(\d+)(\d{3}\b.*)$/, '$1,$2');
    }
    
    return valueText;
}

function dodemographics(id, demographics)
{
    var population = demographics[0][0];
    var housing = demographics[1][0];
    
    $([id, '.population-number'].join(' ')).text(nicenumber(population));
    $([id, '.housing-number'].join(' ')).text(nicenumber(housing));
    
    function raceChart()
    {
        var counts = [], races = [];
        
        for(var i = 2; i <= 8; i += 1)
        {
            var count = nicenumber(100 * demographics[i][0] / population);

            counts.push(count);
            races.push(escape(count + '% ' + demographics[i][1]));
        }
        
        var chart = new Image();

        chart.src = ['http://chart.apis.google.com/chart?cht=p',
                     '&chs=900x150',
                     '&chco=9c9ede|7375b5|4a5584|cedb9c|b5cf6b|8ca252|637939',
                     '&chd=t:', counts.join(','),
                     '&chl=', races.join('|')].join('');
        
        return chart;
    }
    
    function genderChart()
    {
        var counts = [
                      (100 * demographics[9][0] / population).toFixed(1),
                      (100 * demographics[33][0] / population).toFixed(1)
                     ];
        
        var genders = [counts[0] + '% Male', counts[1] + '% Female'];
        
        var chart = new Image();
        
        chart.src = ['http://chart.apis.google.com/chart?cht=p',
                     '&chs=900x100',
                     '&chco=c2e699|31a354',
                     '&chd=t:', counts.join(','),
                     '&chl=', genders.join('|')].join('');
        
        return chart;
    }
    
    function ageChart()
    {
        var counts = [], ages = [];
        
        var blocks = [['Under 18', 10, 13, 34, 37],
                      ['Age 18 to 29', 14, 18, 38, 42],
                      ['Age 30 to 44', 19, 21, 43, 45],
                      ['Age 45 to 64', 22, 26, 46, 50],
                      ['Age 65 and up', 27, 32, 51, 56]];
        
        for(var i = 0; i < blocks.length; i += 1)
        {
            var age = blocks[i][0], count = 0;
            
            for(var j = blocks[i][1]; j <= blocks[i][2]; j += 1)
            {
                count += demographics[j][0];
            }
            
            for(var j = blocks[i][3]; j <= blocks[i][4]; j += 1)
            {
                count += demographics[j][0];
            }
            
            count = nicenumber(100 * count / population);
            
            counts.push(count);
            ages.push(count + '% ' + age);
        }
        
        var chart = new Image();
        
        chart.src = ['http://chart.apis.google.com/chart?cht=p',
                     '&chs=900x150',
                     '&chco=ffffcc|c2e699|78c679|31a354|006837',
                     '&chd=t:', counts.join(','),
                     '&chl=', ages.join('|')].join('');
        
        return chart;
    }
    
    function housingChart()
    {
        var counts = [], houses = [];
        
        var blocks = [['6 and more person households', 62, 63, 70, 71],
                      ['4 and 5 person households', 60, 61, 68, 69],
                      ['Three person households', 59, 59, 67, 67],
                      ['Two person households', 58, 58, 66, 66],
                      ['One person households', -1, -2, 65, 65]];
        
        for(var i = 0; i < blocks.length; i += 1)
        {
            var house = blocks[i][0], count = 0;
            
            for(var j = blocks[i][1]; j <= blocks[i][2]; j += 1)
            {
                count += demographics[j][0];
            }
            
            for(var j = blocks[i][3]; j <= blocks[i][4]; j += 1)
            {
                count += demographics[j][0];
            }
            
            count = nicenumber(100 * count / housing);
            
            counts.push(count);
            houses.push(count + '% ' + house);
        }
        
        var chart = new Image();
        
        chart.src = ['http://chart.apis.google.com/chart?cht=p',
                     '&chs=900x150',
                     '&chco=006837|31a354|78c679|c2e699|ffffcc',
                     '&chd=t:', counts.join(','),
                     '&chl=', houses.join('|')].join('');
        
        return chart;
    }

    $([id, '.race-chart'].join(' ')).empty().append(raceChart());
    $([id, '.gender-chart'].join(' ')).empty().append(genderChart());
    $([id, '.age-chart'].join(' ')).empty().append(ageChart());
    $([id, '.housing-chart'].join(' ')).empty().append(housingChart());
}

function paintbullseye(ctx, x, y)
{
    ctx.fillStyle = 'rgba(0, 0, 0, .1)';

    ctx.beginPath();
    ctx.arc(x, y, 15, 0, Math.PI*2, false);
    ctx.closePath();

    ctx.fill();

    ctx.fillStyle = '#fff';
    ctx.strokeStyle = 'rgba(49, 163, 84, 1)';
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.arc(x, y, 10, 0, Math.PI*2, false);
    ctx.closePath();

    ctx.fill();
    ctx.stroke();
    
    ctx.fillStyle = '#000';

    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI*2, false);
    ctx.closePath();

    ctx.fill();
}

function domap(id, geometry, latlon)
{
    var width = 700, height = 600, mm = com.modestmaps;
    
    var locations = [], points = [];
    
    for(var i = 0; i < geometry.coordinates[0].length; i += 1)
    {
        var coord = geometry.coordinates[0][i];
        locations.push(new mm.Location(coord[1], coord[0]));
    }
    
    $('#' + id).empty();
    
    var template = 'http://otile1.mqcdn.com/tiles/1.0.0/osm/{Z}/{X}/{Y}.png';
    var provider = new mm.TemplatedMapProvider(template);
    var element = document.getElementById(id);
    
    var map = new mm.Map(element, provider, new mm.Point(width, height), []);

    map.setSize(width, height);
    map.setExtent(locations);
    map.draw();
    
    var ymin = height, ymax = 0;
    
    for(var i = 0; i < locations.length; i += 1)
    {
        var point = map.locationPoint(locations[i]);
        points.push(point);
        
        ymin = Math.min(ymin, point.y);
        ymax = Math.max(ymax, point.y);
    }
    
    height = Math.ceil(21 + ymax - ymin);
    
    map.setSize(width, height);
    
    for(var i = 0; i < locations.length; i += 1)
    {
        points[i] = map.locationPoint(locations[i]);
    }
    
    var canvas = document.createElement('canvas');
    canvas.style.position = 'absolute';
    canvas.style.left = 0;
    canvas.style.top = 0;
    canvas.width = width;
    canvas.height = height;
    map.parent.appendChild(canvas);
    
    var ctx = canvas.getContext('2d');
    
    if(ctx)
    {
        ctx.clearRect(0, 0, width, height);
        
        var start = points[points.length - 1];
        
        ctx.fillStyle = 'rgba(255, 255, 255, 1)';
        ctx.beginPath();
        
        ctx.moveTo(0, 0);
        ctx.lineTo(0, height);
        ctx.lineTo(width, height);
        ctx.lineTo(width, 0);
        ctx.lineTo(0, 0);

        ctx.moveTo(start.x, start.y);
        
        for(var i = 0; i < points.length; i += 1)
        {
            ctx.lineTo(points[i].x, points[i].y);
        }
        
        ctx.closePath();
        ctx.fill();
        
        ctx.strokeStyle = 'rgba(49, 163, 84, 1)';
        
        ctx.moveTo(start.x, start.y);
        ctx.beginPath();
        
        for(var i = 0; i < points.length; i += 1)
        {
            ctx.lineTo(points[i].x, points[i].y);
        }
        
        ctx.closePath();
        ctx.stroke();
    }
    
    var location = new mm.Location(latlon[0], latlon[1]);
    var point = map.locationPoint(location);
    
    paintbullseye(ctx, point.x, point.y);
}

function donavmap(id, latlon)
{
    var width = 700, height = 250, mm = com.modestmaps;
    
    $('#' + id).empty();
    
    var template = 'http://otile1.mqcdn.com/tiles/1.0.0/osm/{Z}/{X}/{Y}.png';
    var provider = new mm.TemplatedMapProvider(template);
    var element = document.getElementById(id);
    
    var map = new mm.Map(element, provider, new mm.Point(width, height));

    map.setSize(width, height);
    map.setCenterZoom(new mm.Location(latlon[0], latlon[1]), 14);
    map.draw();
    
    var canvas = document.createElement('canvas');
    canvas.style.position = 'absolute';
    canvas.style.left = 0;
    canvas.style.top = 0;
    canvas.width = width;
    canvas.height = height;
    map.parent.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    
    paintbullseye(ctx, canvas.width/2, canvas.height/2);
    
    return map;
}

function togglenavmap(element)
{
    var container = $('#nav-map-container');
    
    if(container.hasClass('off')) {
        $(element).text('Hide Map');
        container.removeClass('off');

    } else {
        $(element).text('Show Map');
        container.addClass('off');
    }
    
    return false;
}

function tractfinder()
{
    var navmap = undefined,
        latitude = undefined,
        longitude = undefined;

    function navmapzoomin()
    {
        if(navmap)
        {
            navmap.zoomIn();
        }
        
        return false;
    }

    function navmapzoomout()
    {
        if(navmap)
        {
            navmap.zoomOut();
        }
        
        return false;
    }
    
    function onlocation(o)
    {
        //console.log(o);
        
        latitude = o.place.centroid.latitude;
        longitude = o.place.centroid.longitude;
        
        window['onblock'] = onblock;

        var url = ['http://data.fcc.gov/api/block/2000/find',
                   '?format=jsonp',
                   '&latitude=', latitude.toFixed(7),
                   '&longitude=', longitude.toFixed(7),
                   '&callback=?'];

        $('#tract').addClass('loading');
        $('#county').addClass('loading');
        $('#state').addClass('loading');

        $.ajax({
            dataType: 'jsonp',
            url: url.join(''),
            success: onblock
        });
        
        if(navmap == undefined)
        {
            navmap = donavmap('nav-map', [latitude, longitude]);

            var onmoved = getonmoved(navmap);
            navmap.addCallback('zoomed', onmoved);
            navmap.addCallback('panned', onmoved);
            
            $('#navmap-toggle').removeClass('hidden');
        }
    }

    function onblock(o)
    {
        //console.log(['block', o]);
        
        if(!o.Block.FIPS.match(/^(\d{2})(\d{3})(\d{6})(\d{4})/))
        {
            //console.log([o.Block.FIPS, '?!']);
            return;
        }
        
        $('#block .name').text('Block ' + o.Block.FIPS.replace(/^(\d{2})(\d{3})(\d{6})(\d{4})$/, '$1.$2.$3.$4'));

        var tract = o.Block.FIPS.replace(/^(\d{2})(\d{3})(\d{6}).+$/, 'http://this-tract.s3.amazonaws.com/tracts/$1/$2/$3.json');
        var county = o.Block.FIPS.replace(/^(\d{2})(\d{3}).+$/, 'http://this-tract.s3.amazonaws.com/counties/$1/$2.json');
        var state = o.Block.FIPS.replace(/^(\d{2}).+$/, 'http://this-tract.s3.amazonaws.com/states/$1.json');
        
        //console.log(tract);
        //console.log(county);
        //console.log(county);

        $.ajax({
            dataType: 'jsonp',
            url: 'slimjim.php?url=' + escape(tract) + '&callback=?',
            success: ontract
        });
        
        $.ajax({
            dataType: 'jsonp',
            url: 'slimjim.php?url=' + escape(county) + '&callback=?',
            success: oncounty
        });
        
        $.ajax({
            dataType: 'jsonp',
            url: 'slimjim.php?url=' + escape(state) + '&callback=?',
            success: onstate
        });
        
        window['oncounty'] = oncounty;
        window['onstate'] = onstate;
    }

    function ontract(o)
    {
        //console.log(['tract', o]);
        
        $('#tract .name').text(o.Name);
        $('#block .tract-name').text(o.Name);
        $('#tract .landarea-number').html(nicenumber(o.Geography['Land Area'] / 1000000) + ' km<sup>2<'+'/sup>');
        $('#tract .waterarea-number').html(nicenumber(o.Geography['Water Area'] / 1000000) + ' km<sup>2<'+'/sup>');
        
        $('#tract').removeClass('loading');

        dodemographics('#tract', o.Demographics);
        domap('tract-map', o.Geography.geometry, [latitude, longitude]);
    }

    function oncounty(o)
    {
        //console.log(['county', o]);
        
        $('#county').removeClass('loading');

        $('#county .name').text(o.Name);
        $('#block .county-name').text(o.Name);
        $('#county .landarea-number').html(nicenumber(o.Geography['Land Area'] / 1000000) + ' km<sup>2<'+'/sup>');
        $('#county .waterarea-number').html(nicenumber(o.Geography['Water Area'] / 1000000) + ' km<sup>2<'+'/sup>');
        
        dodemographics('#county', o.Demographics);
    }

    function onstate(o)
    {
        //console.log(['state', o]);
        
        $('#state').removeClass('loading');

        $('#state .name').text(o.Name);
        $('#block .state-name').text(o.Name);
        $('#state .landarea-number').html(nicenumber(o.Geography['Land Area'] / 1000000) + ' km<sup>2<'+'/sup>');
        $('#state .waterarea-number').html(nicenumber(o.Geography['Water Area'] / 1000000) + ' km<sup>2<'+'/sup>');
        
        dodemographics('#state', o.Demographics);
    }

    function onLatLonQuery(q)
    {
        q = q.replace(/^\s*(\S.+\S)\s*$/, '$1');
        var latlon = q.split(/[\,\s]+/);
        latlon = [parseFloat(latlon[0]), parseFloat(latlon[1])];
        q = latlon[0].toFixed(6) + ', ' + latlon[1].toFixed(6);
        var loc = {'place': {'centroid': {'latitude': latlon[0], 'longitude': latlon[1]}}};
        onlocation(loc);
        
        return q;
    }
    
    function onPlaceSearch(o)
    {
        //console.log(o);
        
        if(o.results.length)
        {
            var latlon = o.results[0].locations[0].latLng;
            var center = {'latitude': latlon.lat, 'longitude': latlon.lng};
            onlocation({'place': {'centroid': center}});
        }
    }
    
    function onSearchQuery(q)
    {
        var appid = 'Dmjtd|lu612007nq,20=o5-50zah';
        //var appid = unescape('Fmjtd%7Cluu7nu0rn0%2Cag%3Do5-5z1xq');
        
        var url = ['http://www.mapquestapi.com/geocoding/v1/address',
                   '?inFormat=kvp&outFormat=json',
                   '&key=' + escape(appid),
                   '&location=' + escape(q),
                   '&callback=?'];
        
        $.ajax({
            dataType: 'jsonp',
            url: url.join(''),
            success: onPlaceSearch
        });
        
        return q;
    }
    
    function start()
    {
        if(location.hash.match(/^#-?\d+(\.\d+)?,-?\d+(\.\d+)?$/))
        {
            var q = onLatLonQuery(location.hash.substr(1));
            location.href = location.pathname + '?q=' + escape(q);
            
            return;
        }
    
        if(location.search.match(/^\?/))
        {
            var parts = location.search.substr(1).split('&');
            
            for(var i = 0; i < parts.length; i += 1)
            {
                if(parts[i].match(/^q=.+$/))
                {
                    var q = unescape(parts[i].substr(2).replace(/\+/g, '%20'));
                    
                    if(q.match(/^\s*-?\d+(\.\d+)?[\,\s]+-?\d+(\.\d+)?\s*$/)) {
                        q = onLatLonQuery(q);

                    } else {
                        q = onSearchQuery(q);
                    }
                    
                    document.getElementById('location-q').value = q;
                    return;
                }
            }
        }
        
        /*
        var loc = {'place': {'centroid': {'latitude': 40.60274481122281, 'longitude': -75.44689178466797}}}; // testing
        var loc = {'place': {'centroid': {'latitude': 37.804372, 'longitude': -122.270803}}}; // downtown
        var loc = {'place': {'centroid': {'latitude': 37.764863, 'longitude': -122.419313}}}; // 16th & mission
        var loc = {'place': {'centroid': {'latitude': 37.804189, 'longitude': -122.263198}}}; // 17th & jackson
        onlocation(loc);
        */

        yqlgeo.get('visitor', onlocation);
    }
    
    function getonmoved(map)
    {
        var timeout;
        
        function actually()
        {
            //console.log(['center', map.getCenter()]);
            var loc = map.getCenter();
            location.hash = '#' + loc.lat.toFixed(6) + ',' + loc.lon.toFixed(6);
            loc = {'place': {'centroid': {'latitude': loc.lat, 'longitude': loc.lon}}};
            onlocation(loc);
        }
        
        function moved(map)
        {
            window.clearTimeout(timeout);
            timeout = window.setTimeout(actually, 500);
        }
        
        return moved;
    }
    
    return {start: start, navmapzoomin: navmapzoomin, navmapzoomout: navmapzoomout};
}
