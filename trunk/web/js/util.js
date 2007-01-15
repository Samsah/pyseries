function togglePremieres() {
    eps = $$('tr.premiere');
    eps.each(function(row) {
	if(Element.hasClassName(row, 'active')) {
	    Element.removeClassName(row, 'active');
	} else {
	    Element.addClassName(row, 'active');
	}
    });
}

function toggleSerie(element) {
    // toggle selection for this serie
    if(Element.hasClassName(element, 'selected')) {
	Element.removeClassName(element, 'selected');
    } else {
	Element.addClassName(element, 'selected');
    }
	
    // update the shown list
    updateSelections();
}

function deselectAll() {
    $$("#tracklist a.selected").each(function(element) {
	Element.removeClassName(element, 'selected');
    });
    updateSelections();
}

function updateSelections() {
    // find all serie rows
    allseries = $$("#airdates tbody tr");
    // get selected series
    selected = $$("#tracklist a.selected");

    // show them all
    allseries.each(function(row) {
	row.show();
    });

    if(selected.length == 0) {
	Element.update('selectedcount', "");
	Element.hide('deselect');
	return;
    } else {
	Element.update('selectedcount', selected.length+" selected");
	Element.show('deselect');
    }

    // hide all
    allseries.each(function(row) {
	row.hide();
    });
    
    // get all selected serie names
    var series = new Array();
    selected.each(function(element) {
	series.push(element.innerHTML)
    });

    // show only the selected rows
    allseries.each(function(row) {
	if(series.member(row.cells[2].innerHTML)) {
	    row.show();
	}
    });
}

function showSeriesByRegex(regex, modifiers) {
    // find all serie rows
    allseries = $$("#airdates tbody tr");

    allseries.each(function(row) {
	row.hide();
    });
    
    re = new RegExp(regex, modifiers);
    // show only the selected rows
    allseries.each(function(row) {
	if(row.cells[2].innerHTML.match(re) || row.cells[4].innerHTML.match(re)) {
	    row.show();
	}
    });
}

function doSearchFilter(element) {
    showSeriesByRegex(element.value, 'i');
}
