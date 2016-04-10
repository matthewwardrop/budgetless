function block(element) {
	$(element).block({
		message: '<h1>Processing</h1>',
		css: { border: '3px solid #a00' }
	});
}

function unblock(element) {
	$(element).unblock();
}

function load_panel(element, url, blockel,f ) {
	if (typeof blockel == undefined) {
		blockel = element;
	}
	block(blockel);
	$(element).load(url, function () {unblock(blockel); if (typeof f != undefined) f();});
}

function showYearSummary(year) {
	load_panel('#month_list','panel/week_list?year='+year, '#leftpane');
}

function showWeekChart(date) {
	current_date = date;
	load_panel('#toppane_inner','panel/week_chart?date='+date,'#toppane', function () {
		$('.js-plotly-plot').get(0).on('plotly_click', function(data) {
				showDayTransactions(data['points'][0]['x']);
		});
	});
	$('#botpane_inner').empty();

}

function toggleOffBudget(el, id) {
	var parent = $(el).parent();
	parent.toggleClass('offbudget');
	var status = !parent.hasClass('offbudget');
	$.ajax({
		type: "POST",
		url: 'ajax/set_transaction_props',
		data: {'id': id, 'onbudget': status},
		error: function() {
			parent.toggleClass('offbudget');
		},
		success: function() {
			refresh()
		}
	});
}

function resetOffBudget(id) {
	$.ajax({
		type: "POST",
		url: 'ajax/set_transaction_props',
		data: {'id': id, 'onbudget': 'reset'},
		error: function() {
			alert("Failed to reset off budget status!")
		},
		success: function() {
			refresh();
		}
	});
}

function saveNotes(el, id) {
	var notes = $(el).val();
	$.ajax({
	  type: "POST",
	  url: 'ajax/set_transaction_props',
	  data: {'id': id, 'notes': notes},
		error: function() {
			$('#botpane_inner').empty();
		}
	});
}

function showDayTransactions(date) {
	current_day=date;
	load_panel('#botpane_inner','panel/day_transactions?date='+date, '#botpane');
}

function refresh() {
	if (typeof current_date != undefined) showWeekChart(current_date);
	if (typeof current_day != undefined) showDayTransactions(current_day);
}
