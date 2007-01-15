<?php
header("Content-Type: text/html; charset=utf-8");

// get timedelta of the airdate and current date
function getDelta($airdate, $episode) {
        $now = time();
	// figure out the amount of days until next ep
	$td = $airdate-$now;
	$td = intval(strftime("%j", $td));

	if($episode == 1) {
		$style = "premiere";
	} else {
		$style = "normal";
	}

	// append new styles instead of overwriting, so a series can be a "premiere" and "today"
	if($td == 364) {
		$td = "Yesterday";
		$style .= " yesterday";
	} elseif($td == 365) {
		$td = "Today";
		$style .= " today";
	} elseif($td == 1) {
		$td = "Tomorrow";
	} else {
		$td = $td." days";
	}

	$retval = array($td, $style);
	return $retval;
}

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
<title>Series airdates</title>
<script type="text/javascript" src="js/sortabletable.js"></script>
<script type="text/javascript" src="js/util.js"></script>
<script src="js/prototype.js" type="text/javascript"></script>
<script src="js/scriptaculous.js?load=effects" type="text/javascript"></script>
<link type="text/css" rel="StyleSheet" href="css/sortabletable.css" />
<link type="text/css" rel="StyleSheet" href="css/main.css" />
</head>
<body>
<?php
// Open DB
$db = sqlite_open("series.db");
// Get all series from yesterday onwards
$query = sqlite_query($db, "SELECT * FROM series WHERE airdate >= date('now', 'localtime', '-1 day') ORDER BY airdate, serie;");
$series = sqlite_fetch_all($query);
// all series from -7 days to day before yesterday
$query = sqlite_query($db, "SELECT * FROM series WHERE airdate >= date('now', 'localtime', '-7 day') AND airdate < date('now', 'localtime', '-1 day') ORDER BY airdate, serie;");
$past_series = sqlite_fetch_all($query);
?>
<div id="left">
<h1>Series airdates</h1>

<div id="controls">
<ul>
  <li><a href="#" onclick="new Effect.toggle('past_episodes', 'blind'); return false;">Toggle past episodes</a></li>
  <li><a href="#" onclick="togglePremieres(); return false;">Toggle season premieres</a></li>
  <li>Search: <input type="text" onblur="deselectAll()" onkeyup="doSearchFilter(this)" /></li>
</ul>
</div>

<table id="airdates" class="sort-table">
<caption id="selectedcount"></caption>
<thead>
	<tr><td>Diff</td><td>Date</td><td>Series</td><td>Episode</td><td>Title</td></tr>
</thead>
<tbody id="past_episodes" style="display:none">
<?php
foreach($past_series as $serie) {
	printf("\t<tr class='past'><td>%s</td><td>%s</td><td>%s</td><td>%02dx%02d</td><td>%s</td></tr>\n", $td, $serie['airdate'], htmlspecialchars($serie['serie']), $serie['season'], $serie['episode'], htmlspecialchars($serie['title']));
}
?>
</tbody>
<tbody id="current_episodes">
<?php
foreach($series as $serie) 
{
	$airdate = strtotime($serie['airdate']);
	$vals = getDelta($airdate, $serie['episode']);
	$td = $vals[0];
	$style = $vals[1];

	printf("\t<tr class='%s'><td>%s</td><td>%s</td><td>%s</td><td>%02dx%02d</td><td>%s</td></tr>\n", $style, $td, $serie['airdate'], htmlspecialchars($serie['serie']), $serie['season'], $serie['episode'], htmlspecialchars($serie['title']));
}

?>
</tbody>
</table>
</div>

<div id="right">
<div id="tracklist">
<h2>Known series</h2>
<a id="deselect" href="#" style="display:none;font-weight: bold;" onclick="deselectAll(); return false;">[Deselect all]</a>
<ul>
<?php
$res = sqlite_query($db, "SELECT DISTINCT serie FROM series ORDER BY serie;");
$series = sqlite_fetch_all($res);
foreach($series as $serie) {
	printf("\t<li><a href='#' onclick='toggleSerie(this); return false;'>%s</a></li>\n", htmlspecialchars($serie['serie']));
}
?>
</ul>
</div>
</div>

<div id="footer">
<hr/>
Source: <a href="http://epguides.com/">epguides.com</a>
</div>
<?php
sqlite_close($db);
?>
<script type="text/javascript">
  var st = new SortableTable($("airdates"), ["None","Date","String","String","String"]);
  st.setTBody($('current_episodes'))
  st.sort(1);
</script>
<script src="http://www.google-analytics.com/urchin.js" type="text/javascript">
</script>
<script type="text/javascript">
_uacct = "UA-378254-3";
urchinTracker();
</script>
</body>
</html>