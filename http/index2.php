<!Doctype html>
<html class="no-js" lang="en-US">

<head>
  <meta charset="utf-8">
  <meta http-equiv="x-ua-compatible" content="ie=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#ffffff" />
  <!-- <meta http-equiv="refresh" content="30" /> -->

  <title>Aviary Control</title>

    <!--Style CSS-->
    <style>
body {
    font-family: 'Share Tech', sans-serif;
    font-size: 14px;
    color: white;
    align-items: center;
    margin: 0;
    text-shadow: 8px 8px 10px #0000008c;
    background-color: #343a40;
    background-image: url(img/bg.jpg);
}

a {
  color: hotpink;
}

h1 {
    margin: 20px;
}
	.message {
	    font-style: italic;
	    font-size: 16px;
	    margin: 10px;
	    padding: 2px;
	    color: white;
            text-align: center;
	}
    </style>

<script src="https://code.jquery.com/jquery-2.2.4.min.js"></script>

<script>
// shorter syntax for document.ready
$(function () {
	// attach a click event handler
	$('#open_link').click(function(e) {
		// prevent the click from redirecting
		e.preventDefault();
		// make an AJAX request
		$.post($(this).attr('href'), function (res) {
			// handle the response (*) by storing the message into the DIV#message
			$('#msg').html(res);
		});
	});
	$('#close_link').click(function(e) {
		// prevent the click from redirecting
		e.preventDefault();
		// make an AJAX request
		$.post($(this).attr('href'), function (res) {
			// handle the response (*) by storing the message into the DIV#message
			$('#msg').html(res);
		});
	});
});
</script>



    <style>
      .starter-template {
        padding: 40px 15px;
        text-align: center;
      }
      .video-js {
        margin: 0 auto;
      }
    </style>

    <!--[if lt IE 9]>
        <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
        <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
        <![endif]-->

</head>

<body>
<?php

require_once "config.php";

function d($var){
	echo '<pre>';
	var_dump($var);
	echo '</pre>';
}
function getNewestDir($path) {
	$working_dir = getcwd();
	chdir($path); ## chdir to requested dir
	$ret_val = false;
	if ($p = opendir($path) ) {
		while (false !== ($file = readdir($p))) {
			if ($file{0} != '.' && is_dir($file)) {
				#$list[] = date('YmdHis', filemtime($path.'/'.$file)).$path.'/'.$file;
				#$list[] = $path.'/'.$file;
				$list[] = $file;
			}
		}
		rsort($list);
		$ret_val = $list[0];
	}
	chdir($working_dir); ## chdir back to script's dir
	return $ret_val;
}


## Fetch latest image
$latestdir = getNewestDir($timelapse_path);
foreach (glob($timelapse_uri.$latestdir.'/*.jpg') as $f) {
	# store the image name with the last modification time and imagename as a key
	$photos[filemtime($f) . '-' . $f] = $f;
}
$keys = array_keys($photos);
sort($keys);                    # sort is oldest to newest,


## Read state file
$state_data = file_get_contents($state_file);

$decoded_json = json_decode($state_data, false);


?>

<!--<p style="text-align:center"><img alt="" src="<?php echo $photos[array_pop($keys)]; ?>" style="border-style:solid; border-width:1px" /></p>-->



<p style="text-align:center">Door is:&nbsp; <b><?php echo $decoded_json->state; ?></b></p>

<p style="text-align:center"><a id="open_link" href="wrapper.php?dooraction=open">Open door</a> &nbsp; |&nbsp; <a id="close_link" href="wrapper.php?dooraction=closed">Close door</a></p>

<div class="message" id="msg"></div>

<p style="text-align:center">&nbsp;</p>
      <section class="starter-template">
        <video id=example-video width=1280 height=1024 class="video-js vjs-default-skin" controls>
          <source
             src="//stream1.omacks.com/proxied/stream.m3u8"
             type="application/x-mpegURL">
        </video>

      </section>

    <link href="https://unpkg.com/video.js/dist/video-js.css" rel="stylesheet">

    <script src="https://unpkg.com/video.js/dist/video.js"></script>
    <script src="https://unpkg.com/videojs-flash/dist/videojs-flash.js"></script>
    <script src="https://unpkg.com/videojs-contrib-hls/dist/videojs-contrib-hls.js"></script>
    <script src='videojs.zoomrotate.js'></script>

    <script>
      (function(window, videojs) {
        var player = window.player = videojs('example-video');

        // hook up the video switcher
        var loadUrl = document.getElementById('load-url');
        var url = document.getElementById('url');
        loadUrl.addEventListener('submit', function(event) {
          event.preventDefault();
          player.src({
            src: url.value,
            type: 'application/x-mpegURL'
          });
          return false;
        });
      }(window, window.videojs));
    </script>
    <script>
      player.zoomrotate({
        rotate: 180,
      });
    </script>
</body>
</html>
