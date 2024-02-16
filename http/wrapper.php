<?php
require_once "config.php";

function is_ajax() {
	return isset($_SERVER['HTTP_X_REQUESTED_WITH']) && strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest';
}

## Read state file
$state_data = file_get_contents($state_file);
$decoded_json = json_decode($state_data, false);
$doorstate = $decoded_json->state;

// check if the request was made via AJAX
if (is_ajax() && isset($_GET['dooraction'])) {

	if ($_GET['dooraction'] == $doorstate) {
		echo "The door is already ".$doorstate;
	        exit;

	}
	elseif ($_GET['dooraction'] == "open") {
		echo "opening...";
		$command = escapeshellcmd($open_cmd);
		$out = shell_exec($command);
		echo $out;
	}
	elseif ($_GET['dooraction'] == "closed") {
		echo "closing...";
		$command = escapeshellcmd($close_cmd);
		$out = shell_exec($command);
		echo $out;
	}
	// stop the script from outputting the rest
}
?>
