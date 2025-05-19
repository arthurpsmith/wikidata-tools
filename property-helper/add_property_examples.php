<?php 
// Copyright 2025 Arthur P. Smith
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

function remove_html_comments($content = '') {
	return preg_replace('/<!--(.|\s)*?-->/', '', $content);
}

function extract_templates($content, &$template_list) {
	$tindex = 1;
	while (str_contains($content, "{{")) {
		$matches = [];
		preg_match('/{{([^}]*)}}/', $content, $matches);
		$template_list[$tindex] = $matches[1];
		$content = str_replace($matches[0], "%%{$tindex}%%", $content);
		$tindex += 1;
	}
	return $content;
}

function add_key_value_to_array($field_line, &$array) {
	$key_value = array();
	$parts = explode('=', $field_line);
	if (count($parts) > 1) {
		$key = trim(array_shift($parts));
		$value = trim(implode('=', $parts));
		if ($value != '') {
	                $array[$key] = $value;
		}
        }
}

function reinsert_templates_in_string_value($template_list, $content) {
	while (str_contains($content, "%%")) {
		$matches = [];
		preg_match('/%%(\d+)%%/', $content, $matches);
		$template_content = $template_list[$matches[1]];
		$content = str_replace($matches[0], $template_content, $content);
	}
	return $content;
}

function format_object_by_datatype($datatype, $value) {
	$formatted_value = $value;
	switch($datatype) {
		case 'external-id':
		case 'string':
		case 'media':
		case 'URL':
		case 'mathematical expression':
		case 'musical-notation':
			$formatted_value = "\"{$value}\"";
			break;
		case 'time':
			$formatted_value = "+{$value}";
			break;
		case 'globe-coordinate':
			$formatted_value = "@{$value}";
			break;
	}
	return $formatted_value;
}

function proposal_examples_to_qs_string($proposal_text, $property_id) {
	$proposal = preg_replace('/^{{/', '', $proposal_text);
	$proposal = preg_replace('/}}$/', '', $proposal);
	$template_list = [];
	$proposal = extract_templates($proposal, $template_list);
	$proposal_lines = explode("|", $proposal);

	$proposal_fields = array();
	foreach ($proposal_lines as $field_line) {
		add_key_value_to_array($field_line, $proposal_fields);
	}

	foreach ($template_list as $index => $template_line) {
		$template_parts = explode("|", $template_line);
		$adjusted_value = $template_line;
		switch(trim($template_parts[0])) {
			case 'P':
			case 'Pfr':
				$adjusted_value = 'P' . 
					str_replace('P', '', $template_parts[1]);
				break;
			case 'Q':
			case 'Q\'':
			case 'Qfr':
				$adjusted_value = 'Q' . 
					str_replace('Q', '', $template_parts[1]);
				break;
			case 'Statement':
			case 'statement':
			case 'claim':
				$subject = trim($template_parts[1]);
				$object = trim($template_parts[3]);
				$adjusted_value = "$subject - $object";
				break;
			case 'TranslateThis':
				$language_values = [];
				foreach ($template_parts as $field_line) {
					add_key_value_to_array($field_line, $language_values);
				}
				$adjusted_value = $language_values;
				break;
		}
		$template_list[$index] = $adjusted_value;
	}
	
	$qs_commands = "";
	$datatype = $proposal_fields['datatype'];

	foreach (array_keys($proposal_fields) as $field) {
		if (str_starts_with($field, 'example')) {
			$example_data = $proposal_fields[$field];
			$example_data = reinsert_templates_in_string_value($template_list,
				$example_data);
			$example_parts = preg_split('/\s+/', $example_data);
			$example_subject = $example_parts[0];
			$example_object = $example_parts[array_key_last($example_parts)];
			$matches = [];
			if (preg_match('/(\S+)\]/', $example_object, $matches)) {
				$example_object = $matches[1];
			}
			$formatted_example_object = format_object_by_datatype($datatype, $example_object);
			
			$example_property_id = NULL;
			if (str_starts_with($example_subject, 'Q')) {
				$example_property_id = 'P1855';
			}
			if (str_starts_with($example_subject, 'P')) {
				$example_property_id = 'P2271';
			}
			if (str_starts_with($example_subject, 'L')) {
				$example_property_id = 'P5192';
			}
			if (str_starts_with($example_subject, 'commons:') ||
				str_starts_with($example_subject, 'File:')) {
				$example_property_id = 'P6685';
			}
			if ($example_property_id) {
				$qs_commands .= "{$property_id}\t{$example_property_id}\t{$example_subject}\t{$property_id}\t{$formatted_example_object}\n";
			}
		}
	}
	return $qs_commands;
}

function print_footer() {
	print "The <a href=\"https://github.com/arthurpsmith/wikidata-tools/tree/master/property-helper\">source code for this service</a> is available under the <a href=\"http://www.apache.org/licenses/LICENSE-2.0\">Apache License, Version 2.0</a>." ;
	print "</body></html>";
}

print "<html><head>
<meta charset='utf-8'>
<link rel='stylesheet' href='https://tools-static.wmflabs.org/cdnjs/ajax/libs/twitter-bootstrap/4.0.0-beta.2/css/bootstrap.min.css'>
<title>Property Creation Helper</title></head>" ;
print "<body style='margin:10;padding:10'><a href='/'><h1>Wikidata Property Creation Helper</h1></a>" ;

$proposal_url = isset($_REQUEST['proposal_url']) ? $_REQUEST['proposal_url'] : '' ;
$property_id = isset($_REQUEST['property_id']) ? $_REQUEST['property_id'] : '' ;
if (empty($proposal_url) || empty($property_id)) {
	print "ERROR: Property proposal URL or id are missing - please retry!\n";
	print "<hr>";
	print_footer();
	exit();
}

$proposal_file = file_get_contents($proposal_url . '?action=raw');

$proposal_file = remove_html_comments($proposal_file);

$proposal_sections = [];
$pf_parts = preg_split("/==+/", $proposal_file);
foreach ($pf_parts AS $index => $pf_part) {
	if (preg_match('/\s*{{\s*Property proposal/', $pf_part)) {
		$proposal_sections[] = ['label' => $pf_parts[$index-1],
			'proposal' => trim($pf_part)];
	}
}

foreach ($proposal_sections AS $index => $proposal_section) {
	$qs_commands = proposal_examples_to_qs_string(
		$proposal_section['proposal'], $property_id);

	$quickstatements_api_url = 'https://quickstatements.toolforge.org/api.php';
	print "<div>Examples {$index}</div>";
	print "<div><form method='post' class='form' action='$quickstatements_api_url' target='_blank'>";
	print "<input type='hidden' name='action' value='import' />" ;
	print "<input type='hidden' name='temporary' value='1' />" ;
	print "<input type='hidden' name='openpage' value='1' />" ;
	print "<div>Quickstatements V1 commands for creating property:</div>" ;
	print "<div><textarea name='data' cols=80 rows=30>" . $qs_commands . "</textarea></div>";
	print "<div><input type='submit' class='btn btn-primary' name='qs' value='Send to Quickstatements' /></div>";
	print "</form></div>";
	print "<div>Don't forget to add the {{Property documentation}} template on the Property Talk page.</div>";
	print "<div>The <a href='$proposal_url'>original proposal</a> also needs to be updated with the new property id.</div><hr>";
}

print_footer();

?>
