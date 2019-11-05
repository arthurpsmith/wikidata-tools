<?PHP
// Copyright 2016,2017 Arthur P. Smith
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

// See https://www.wikidata.org/wiki/MediaWiki:Gadget-AuthorityControl.js
// for a number of the conversions done here.

$property = isset($_REQUEST['p']) ? $_REQUEST['p'] : '' ;
$url_prefix = isset($_REQUEST['url_prefix']) ? $_REQUEST['url_prefix'] : '' ;
$url_suffix = isset($_REQUEST['url_suffix']) ? $_REQUEST['url_suffix'] : '' ;
$url = rawurldecode(isset($_REQUEST['url']) ? $_REQUEST['url'] : '') ;
$exp = rawurldecode(isset($_REQUEST['exp']) ? $_REQUEST['exp'] : '');
$id = rawurldecode(isset($_REQUEST['id']) ? $_REQUEST['id'] : '') ;

if (! empty($id) ) {
 switch($property) {
  case 213: // ISNI
    $link_string = str_replace(" ", "", $id) ;
    break ;
  case 345: // IMDB
    switch(substr($id, 0, 2)) {
      case 'nm':
        $link_string = "name/$id/";
        break;
      case 'tt':
        $link_string = "title/$id/";
        break;
      case 'ch': # Note - updated October 2018 to redirect to archive.org
        $link_string = "character/$id/";
        $url_prefix = "https://web.archive.org/web/https://www.imdb.com/";
        break;
      case 'ev':
        $link_string = "event/$id";
        break;
      case 'co':
        $link_string = "company/$id/";
        break;
      case 'ni':
        $link_string = "news/$id/";
        break;
      default:
        $link_string = "/$id" ;
        break;
    }
    break;
  case 502: // HURDAT
    $year = substr($id, 4, 4);
    if (intval($year) < 2005) {
        $link_string = $year . '/'; # Can only link to list for year
    } else {
        $id_in_year= strtolower(substr($id, 0, 4));
        $link_string = "$year/$id_in_year/";
    }
    break;
  case 628: // E number
  case 1323: // TA98
    $link_string = substr($id, 1); // Skip initial letter
    break;
  case 679: // ZVG number needs to be padded to 6 digits (leading 0's)
    $link_string = sprintf('%06d', $id);
    break;
  case 882: // FIPS
    $link_string = substr($id, 0, 2) . "/$id";
    break;
  case 919: // SOC code
    $link_string = str_replace("-", "", $id) ;
    break;
  case 1209: // CN
    if (substr($id, 3, 1)==="0") { # for newspapers
        $newspaper_id = str_replace("-", "", $id);
        $link_string = "typeNum=1&pubCode=$newspaper_id";
    } else { # for magazines
        $link_string = "typeNum=2&pubCode=$id";
    }
    break;
  case 2698: // CricketArchive
    if (is_numeric($id)) {
      if (strlen($id) > 3){
        $trunc = substr($id, 0, -3) ;
      } else {
        $trunc = "0";
      }
      $link_string = "$trunc/$id/$id";
    } else {
      $link_string = $id;
    }
    break;
  case 3608: // EU VAT number
    $member_state_code = substr($id, 0, 2);
    $vat_digits = substr($id, 2);
    $link_string = "$member_state_code&number=$vat_digits";
    break;
  case 3723: // USCG Lighthouse ID
    preg_match('/(\d+)-(\d+(?:.\d*)?)/', $id, $a);
    $link_string = "https://msi.nga.mil/queryResults?publications/uscgll?volume=".$a[1]."&featureNumber=".$a[2]."&includeRemovals=false&output=html";
    break;    
  case 4033: // Mastodon address
    $mastodon_parts = split("@", $id);
    $m_user = $mastodon_parts[0];
    $m_host = $mastodon_parts[1];
    $link_string = "http://$m_host/@$m_user";
    break;
  case 5892: // UOL Brazil election id
    $uol_parts = split("/", $id);
    $uol_year = $uol_parts[0];
    $uol_first_code = $uol_parts[1];
    $uol_second_code = $uol_parts[2];
    $uol_third_code = $uol_parts[3];
    $link_string = "ano-eleicao=$uol_year&dados-cargo-disputado-id=$uol_first_code&dados-uf-eleicao=$uol_second_code&dados-municipio-ibge-id=$uol_third_code";
    break;
  case 6371: // Archives of Maryland Biographical Series ID
    $first_digits = substr($id, 0, 3);
    $link_string = "0" . $first_digits . "00/0$id/html/msa$id.html" ;
    break;
  case 6460: // Swedish Organization Number
    $link_string = str_replace("-", "", $id) ;
    break;
  case 6623: // Gamepedia article ID
    $gp_parts = split(":", $id);
    $wiki = $gp_parts[0];
    $page = $gp_parts[1];
    $link_string = "https://$wiki.gamepedia.com/$page";
    break;
  case 6841: // ITF tournament ID
    $itf_parts = split(":", $id);
    $sex = $itf_parts[0];
    $id = $itf_parts[1];
    $link_string = "https://www.itftennis.com/procircuit/tournaments/$sex's-tournament/info.aspx?tournamentid=$id";
    break;
  case 6996: // Epitafier.se ID
    switch(substr($id, 0, 1)) {
      case 'B':
        $link_string = "http://www.epitafier.se/?page=begravningsvapen&subj=$id";
        break;
      case 'E':
        $link_string = "http://www.epitafier.se/?page=epitafier&subj=$id";
        break;
      default:
        $link_string = "http://www.epitafier.se/?page=begravningsvapen&subj=$id" ;
        break;
    }
    break;
  case 1695: // NLP ID
    switch(substr($id, 0, 1)) {
      case 'A':
        $link_string = "http://mak.bn.org.pl/cgi-bin/KHW/makwww.exe?BM=1&NU=1&IM=5&WI=$id" ;
        break;
      case '9':
        $link_string = "http://mak.bn.org.pl/cgi-bin/KHW/makwww.exe?BM=1&NU=1&IM=4&WI=$id" ;
        break;
    }
    break;
  default:
    if (! empty($exp) ) {
      preg_match('/'.$exp.'/', $id, $a);
      for($i=0; $i<sizeof($a); $i++) {
        $url = str_replace("%".$i, $a[$i], $url);
      }
      $link_string = $url;
    }
    else
      $link_string = $id ;
    break;
    

    break ;
 }

 $redirect_url = $url_prefix . $link_string . $url_suffix ;
 header("Location: $redirect_url");
 exit();
}

print "<html><head><meta charset='utf-8'><title>Wikidata External ID redirector</title></head>" ;
print "<body><h1>Wikidata External ID redirector</h1>" ;
print "This accepts the following '?' parameters and returns a redirect constructed from them:" ;
print "<ul>" ;
print "<li> p - property number (eg. 213 = ISNI)</li>";
print "<li> url_prefix - eg. http://isni.org/</li>";
print "<li> url_suffix - eg. .html</li>";
print "<li> id - the id value of this external id property for an entity of interest</li>";
print "</ul>";

$url   = "http://test.org/?vol=%1&item=%2";
$id    = "113-1250";
$exp = "(.*)-(.*)";

print "This accepts the alternative '?' parameters:" ;
print "<ul>" ;
print "<li> url - url with parameters %1, %2... eg. <i>".$url."</i></li>";
print "<li> exp - regular expression eg. <i>".$exp."</i></li>";
print "<li> id - eg. <i>".$id."</i></li>";
$p = "?url=".urlencode($url)."&exp=".urlencode($exp)."&id=".urlencode($id);
print "<li> example <a href='index.php".$p."'>http://tools.wmflabs.org/wikidata-externalid-url/".$p."</a></li>";
$r = "http://test.org/?vol=113?item=1250";
print "<li> result  <a href='".$r."'>".$r."</a></li>";
print "</ul>";
print "Note: all parameters should be url encoded.<br/>";
print "Note: this script also URL-decodes the id value so that an id with several embedded parameters can be used as originally intended.";

print "<p>An example: <a href=\"index.php?p=213&url_prefix=http://isni.org/&id=0000 0000 8045 6315\">http://tools.wmflabs.org/wikidata-externalid-url/?p=213&url_prefix=http://isni.org/&id=0000 0000 8045 6315</a>.</p>";

print "<p>Currently supported id translations:</p>";
print "<ul>";
print "<li>ISNI - property 213</li>";
print "<li>IMDB - property 345</li>";
print "<li>HURDAT - property 502</li>";
print "<li>E number - property 628</li>";
print "<li>SOC code - property 919</li>";
print "<li>CN - property 1209</li>";
print "<li>TA98 - property 1323</li>";
print "<li>CricketArchive - property 2698</li>";
print "<li>EU VAT number - property 3608</li>";
print "<li>USCG Lighthouse ID - property 3723</li>";
print "<li>Mastodon - property 4033</li>";
print "<li>UOL Brazil election id - property 5892</li>";
print "<li>Swedish Organization Number - property 6460</li>";
print "<li>Gamepedia article ID - property 6623</li>";
print "<li>ITF tournament ID - property 6841</li>";
print "<li>Epitafier.se ID - property 6996</li>";
print "<li>NLP ID - property 1695</li>";
print "</ul>";

print "The <a href=\"https://github.com/arthurpsmith/wikidata-tools/tree/master/wikidata-externalid-url\">source code for this service</a> is available under the <a href=\"http://www.apache.org/licenses/LICENSE-2.0\">Apache License, Version 2.0</a>." ;

print "</body></html>";

?>
