<?php

//////////////////////////////////////////////////////////////////////
// Quick tool to apply source-to-source transformation changes
// generated by rosetta-refactor-tool
//////////////////////////////////////////////////////////////////////

if(count($_SERVER['argv']) < 3) {
	echo "Usage: {$_SERVER['argv'][0]} <change log file> <output dir>\n";
	exit;
}

list($me, $change_filename, $output_dir) = $_SERVER['argv'];

$files = [];
foreach(file($change_filename) as $line) {
	list($filename, $offset, $length, $replacement) = explode("\t", rtrim($line), 4);
	if(!$filename || !$offset || !$length || !$replacement) {
		echo "Invalid line: $line";
		continue;
	}
	
	if(!isset($files[$filename]))
		$files[$filename] = [
			'offsets' => [], 
			'content' => file_get_contents($filename),
			'changes' => 0,
		];
		
	$file = &$files[$filename];
	$content = &$file['content'];

	$offset_delta = 0;
	if(isset($file['offsets']))
		foreach($file['offsets'] as $o)
			if($o[0] <= $offset)
				$offset_delta += $o[1];
				
	if($length >= 4294967295) { // -1
		// guess length from cross-file boundaries
		$length = strlen(strtok(substr($content, $offset + $offset_delta), ";\n"));
		// echo "Fixed length: $length\n";
	}

	$replacement = str_replace('\n', "\n", $replacement);
	$content =
		substr($content, 0, $offset + $offset_delta) . 
		$replacement .
		substr($content, $offset + $offset_delta + $length);
	
	$this_delta = strlen($replacement) - $length;
	if($this_delta != 0)
		$file['offsets'][] = [ (int)$offset, $this_delta ];
	$file['changes']++;
}

foreach($files as $filename => $file) {
	
	$rel_filename = substr(strstr($filename, 'source/'), 7);
	$output_filename = $output_dir . '/' . $rel_filename;
	$output_dirname = substr($output_filename, 0, -strlen(strrchr($output_filename, '/')));
	if(!is_dir($output_dirname))
		mkdir($output_dirname, 0755, true);
	
	echo "{$output_filename}: {$file['changes']} changes -- ",
		file_put_contents($output_filename, $file['content']) ? 'OK' : 'ERROR',
		"\n";
}
