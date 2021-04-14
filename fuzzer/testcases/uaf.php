<?php 
$a = null; // the problem only occurs when set to NULL

class gft{
	private $strVal = 'abcd ';	
	public function info(){
	}
}

function test($str, $pad) {
	$x = $str.str_repeat($pad, 8);
	
 	$gft = new gft();
	$gft->info();
	
	var_dump($x);
} 

test($a, 'x');
