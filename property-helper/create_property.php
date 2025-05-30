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

# Translate datatypes from property template format to wikibase json values
function fixed_datatype($datatype_in) {
	$datatype_out = $datatype_in;
	switch($datatype_in) {
		case 'External identifier':
			$datatype_out = 'external-id';
			break;
		case 'Item':
		case 'item':
			$datatype_out = 'wikibase-item';
			break;
		case 'URL':
			$datatype_out = 'url';
			break;
		case 'media':
			$datatype_out = 'commonsMedia';
			break;
		case 'monolingual text':
			$datatype_out = 'monolingualtext';
			break;
		case 'property':
			$datatype_out = 'wikibase-property';
			break;
		case 'tabular':
			$datatype_out = 'tabular-data';
			break;
		case 'mathematical expression':
			$datatype_out = 'math';
			break;
		case 'lexeme':
			$datatype_out = 'wikibase-lexeme';
			break;
		case 'sense':
			$datatype_out = 'wikibase-sense';
			break;
		case 'form':
			$datatype_out = 'wikibase-form';
			break;
	}
	return $datatype_out;
}

function label_and_proposal_to_qs_string($label_text, $proposal_text, $proposal_url) {
	$label_template_list = [];
	$label = extract_templates($label_text, $label_template_list);
	$label_lines = explode("|", $label_template_list[1]);
	$labels = array();
	foreach ($label_lines as $field_line) {
		add_key_value_to_array($field_line, $labels);
	}

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

	$status = $proposal_fields['status'];
	if ($status != 'ready') {
		return "PROPOSAL CANNOT BE CREATED: 'status' is not 'ready'";
	}
	$datatype = fixed_datatype($proposal_fields['datatype']);
	if (empty($datatype)) {
		fwrite(STDERR, "Error: datatype not set in proposal");
		return "PROPOSAL CANNOT BE CREATED: 'datatype' not set";
	}
	$qs_commands .= "CREATE_PROPERTY\t{$datatype}\n";
	foreach ($labels AS $lang => $lang_label) {
		if ($lang == 'anchor') continue;
		$qs_commands .= "LAST\tL{$lang}\t\"$lang_label\"\n";
	}
	$description = $proposal_fields['description'];
	$matches = [];
	if (preg_match('/%%(\d+)%%/', $description, $matches)) {
	    $template_id = $matches[1];
	    $descriptions = $template_list[$template_id];
	    foreach ($descriptions AS $lang => $lang_label) {
		if ($lang == 'anchor') continue;
		$qs_commands .= "LAST\tD{$lang}\t\"$lang_label\"\n";
	    }
	} else {
		$qs_commands .= "LAST\tDen\t\"$description\"\n";
	}
	$qs_commands .= "LAST\tP3254\t\"$proposal_url\"\n";
	if (array_key_exists('formatter URL', $proposal_fields)) {
		$qs_commands .= "LAST\tP1630\t\"{$proposal_fields['formatter URL']}\"\n";
	}
	if (array_key_exists('source', $proposal_fields)) {
		$qs_commands .= "LAST\tP1896\t\"{$proposal_fields['source']}\"\n";
	}
	if (array_key_exists('subject item', $proposal_fields)) {
		$wp_value = reinsert_templates_in_string_value($template_list,
			$proposal_fields['subject item']);
		foreach (preg_split('/\s+/', $wp_value) as $project) {
			$qs_commands .= "LAST\tP1629\t{$project}\n";
		}
	}
	if (array_key_exists('expected completeness', $proposal_fields)) {
		$ec_value = reinsert_templates_in_string_value($template_list,
			$proposal_fields['expected completeness']);
		$qs_commands .= "LAST\tP2429\t{$ec_value}\n";
	}
	if (array_key_exists('applicable stated in value', $proposal_fields)) {
		$si_value = reinsert_templates_in_string_value($template_list,
			$proposal_fields['applicable stated in value']);
		$qs_commands .= "LAST\tP9073\t{$si_value}\n";
	}
	if (array_key_exists('see also', $proposal_fields)) {
		$sa_value = reinsert_templates_in_string_value($template_list,
			$proposal_fields['see also']);
		foreach (preg_split('/\s+/', $sa_value) as $property) {
			$qs_commands .= "LAST\tP1659\t{$property}\n";
		}
	}
	if (array_key_exists('Wikidata project', $proposal_fields)) {
		$wp_value = reinsert_templates_in_string_value($template_list,
			$proposal_fields['Wikidata project']);
		foreach (preg_split('/\s+/', $wp_value) as $project) {
			$qs_commands .= "LAST\tP6104\t{$project}\n";
		}
	}
	
# Constraints:
	$constraint_prop = 'P2302';
	if ($datatype == 'external-id') { # Type and standard boiler-plate constraints for ids
		$property_type = 'Q19847637';
		if (array_key_exists('implied notability', $proposal_fields)) {
			$tvalue = reinsert_templates_in_string_value($template_list,
				$proposal_fields['implied notability']);
			if (str_starts_with($tvalue, 'Q')) {
				$property_type = $tvalue;
			}
		}
		$qs_commands .= "LAST\tP31\t{$property_type}\n";
	    # allowed entity type = wikibase-item
		$qs_commands .= "LAST\t{$constraint_prop}\tQ52004125\tP2305\tQ29934200\n";
	    # allowed scope = as main value or reference
		$qs_commands .= "LAST\t{$constraint_prop}\tQ53869507\tP5314\tQ54828448\tP5314\tQ54828450\n";
	}

	if (array_key_exists('single value constraint', $proposal_fields)) {
		if ($proposal_fields['single value constraint'] == 'yes') {
			$qs_commands .= "LAST\t{$constraint_prop}\tQ19474404\n";
		}
	}
	if (array_key_exists('distinct values constraint', $proposal_fields)) {
		if ($proposal_fields['distinct values constraint'] == 'yes') {
			$qs_commands .= "LAST\t{$constraint_prop}\tQ21502410\n";
		}
	}
	if (array_key_exists('allowed values', $proposal_fields)) {
		$allowed = $proposal_fields['allowed values'];
		$qs_commands .= "LAST\t{$constraint_prop}\tQ21502404\tP1793\t\"{$allowed}\"\n";
	}
	if (array_key_exists('domain', $proposal_fields)) { # Subject type constraint
		$dvalue = reinsert_templates_in_string_value($template_list,
			$proposal_fields['domain']);
		if (str_starts_with($dvalue, 'Q')) {
			$qs_commands .= "LAST\t{$constraint_prop}\tQ21503250\tP2308\t{$dvalue}\tP2309\tQ21503252\n";
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
if (empty($proposal_url)) {
	print "<form method='post' class='form form-inline'>
<div>Proposal URL: <input size=80 name='proposal_url' type='text' /></div>
<div><input type='submit' class='btn btn-primary' name='doit' value='Process proposal' /></div>";
        print "</form>";
	print_footer();
	exit();
}

$proposal_file = file_get_contents($proposal_url . '?action=raw');

$proposal_file = remove_html_comments($proposal_file);

$proposal_sections = [];
$pf_parts = preg_split("/==+/", $proposal_file);
foreach ($pf_parts AS $index => $pf_part) {
	if (preg_match('/\s*{{\s*Property proposal/i', $pf_part)) {
		$proposal_sections[] = ['label' => $pf_parts[$index-1],
			'proposal' => trim($pf_part)];
	}
}

foreach ($proposal_sections AS $index => $proposal_section) {
	$qs_commands = label_and_proposal_to_qs_string(
		$proposal_section['label'], $proposal_section['proposal'],
		$proposal_url);

	$quickstatements_api_url = 'https://quickstatements.toolforge.org/api.php';
	print "<div>Proposal {$index}</div>";
	print "<div><form method='post' class='form' action='$quickstatements_api_url' target='_blank'>";
	print "<input type='hidden' name='action' value='import' />" ;
	print "<input type='hidden' name='temporary' value='1' />" ;
	print "<input type='hidden' name='openpage' value='1' />" ;
	print "<div>Quickstatements V1 commands for creating property:</div>" ;
	print "<div><textarea name='data' cols=80 rows=30>" . $qs_commands . "</textarea></div>";
	print "<div><input type='submit' class='btn btn-primary' name='qs' value='Send to Quickstatements' /></div>";
	print "</form></div>";
	print "<div>Examples need the new property id, please enter it here and submit to add them:</div>";
	print "<div><form method='post' class='form form-inline' action='add_property_examples.php' target='_blank'>";
	print "<input type='hidden' name='proposal_url' value='$proposal_url' />";
	print "New Property ID (i.e. Pxxxx): <input name='property_id' />";
	print "<input type='submit' class='btn btn-primary' name='ex' value='Prepare Examples' />";
	print "</form></div>";
	print "<div>Don't forget to add the {{Property documentation}} template on the Property Talk page.</div>";
	print "<div>The <a href='$proposal_url'>original proposal</a> also needs to be updated with the new property id.</div><hr>";
}

print_footer();

?>
