<?php

    ini_set('include_path', ini_get('include_path').PATH_SEPARATOR.'/usr/share/pear');

    require_once 'PEAR.php';
    require_once 'Net/URL.php';
    require_once 'HTTP/Request.php';

    $url = new Net_URL($_GET['url']);
    $callback = preg_replace('/[^\w_\.]/', '_', $_GET['callback']);
    $hosts = array('this-tract.s3.amazonaws.com');
    
    if(PEAR::isError($url))
    {
        header('HTTP/1.1 400');
        header('Content-Type: text/plain');
        die("{$url->msg}\n");
    }
    
    if(!in_array($url->host, $hosts))
    {
        header('HTTP/1.1 400');
        header('Content-Type: text/plain');
        die("Unrecognized hostname: {$url->host}.\n");
    }
    
    $req = new HTTP_Request($url->getURL());
    $res = $req->sendRequest();
    $code = $req->getResponseCode();
    $type = $req->getResponseHeader('content-type');
    
    if(!in_array($code, array(200, 201)))
    {
        header('HTTP/1.1 400');
        header('Content-Type: text/plain');
        die("Bad response code from {$url->host}: {$code}.\n");
    }
    
    if(!in_array($type, array('text/json', 'application/json')))
    {
        header('HTTP/1.1 400');
        header('Content-Type: text/plain');
        die("Bad response type from {$url->host}: {$type}.\n");
    }
    
    header('HTTP/1.1 200');
    header('Cache-Control: public');
    header('Content-Type: text/javascript');
    header('Last-Modified: '.$req->getResponseHeader('last-modified'));
    header('Date: '.$req->getResponseHeader('date'));
    header('Etag: '.$req->getResponseHeader('etag'));
    printf("%s(%s);\n", $callback, $req->getResponseBody());
    exit();

?>
