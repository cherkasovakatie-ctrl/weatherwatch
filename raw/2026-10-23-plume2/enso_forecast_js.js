function enso_element_show(el) {
    $('#enso-quicklook').hide();
    $('#enso-cpc_update').hide();
    $('#enso-iri_update').hide();
    $('#enso-iri_plume').hide();
    $('#enso-cpc_plume').hide();
    $('#enso-sst_table').hide();
    $('#enso-sst_image').hide();
    $('#enso-iod_forecast').hide();
    $('#enso-nmme').hide();
    $('#enso-contact').hide();

    el.show();
    // History.pushState({location:el});
}

jQuery( document ).ready(function($) {
	// Determine which (if any) page section is desired
	var query = $(location).attr('search');
	var tab = query.match(/enso-.*/);
	if (tab) {
		tab = '#'+tab;
	    enso_element_show( $(tab) );
	} else {
	    enso_element_show( $('#enso-quicklook') );
	}
});
