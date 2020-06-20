window.onload = function() {
    var theme = getCookie( 'theme' );
    if( theme ){
        var themeToggler = document.getElementById("web-theme-toggle");
        if ( theme == 'light' ){themeToggler.checked = true;themeToggler.click();}
        else{themeToggler.checked = false;themeToggler.click()}
    }
}

function setCookie( name, value, daysToLive ) {
    // Encode value in order to escape semicolons, commas, and whitespace
    var cookie = name + "=" + encodeURIComponent(value);
    
    if(typeof daysToLive === "number") {
        /* Sets the max-age attribute so that the cookie expires
        after the specified number of days */
        cookie += "; max-age=" + (daysToLive*24*60*60);
        
        document.cookie = cookie;
    }
}

function getCookie( name ) {
    // Split cookie string and get all individual name=value pairs in an array
    var cookieArr = document.cookie.split(";");
    
    // Loop through the array elements
    for(var i = 0; i < cookieArr.length; i++) {
        var cookiePair = cookieArr[i].split("=");
        
        /* Removing whitespace at the beginning of the cookie name
        and compare it with the given string */
        if(name == cookiePair[0].trim()) {
            // Decode the cookie value and return
            return decodeURIComponent(cookiePair[1]);
        }
    }
    
    // Return null if not found
    return null;
}

document.getElementById("chatToggle").addEventListener("click", function() {
    var x = document.getElementById("chatWindow");
    if ( x.classList.contains('d-none') ) {
        x.classList.remove('d-none');
    } else {
        x.classList.add('d-none');
    }
});

document.getElementById("web-theme-toggle").addEventListener("change",function(){
    var elems_dark = document.querySelectorAll('.theme-dark');
    var elems_light = document.querySelectorAll('.theme-light');
    var singleFormBtn = document.querySelector('#singleEntryForm button[type="submit"]');
    
    if( this.checked )
    {
        Array.prototype.forEach.call( elems_light, function( elem ){
            elem.classList.remove( 'theme-light' );
            elem.classList.add( 'theme-dark' );
        });
        Array.prototype.forEach.call( document.getElementsByClassName('navbar-light'), function( elem ){
            elem.classList.add('navbar-dark');
            elem.classList.remove('navbar-light');
        });
        Array.prototype.forEach.call( document.getElementsByTagName('hr'), function( elem ){
            elem.classList.add('bg-white');
            elem.classList.remove('bg-dark');
        });
        Array.prototype.forEach.call( document.querySelectorAll('nav .dropdown-item'), function( elem ){
            elem.classList.add('text-white');
        });
        singleFormBtn.classList.remove('btn-light', 'btn-outline-dark');
        singleFormBtn.classList.add('btn-dark');

        setCookie('theme', 'dark', 30);
    }
    else
    {
        Array.prototype.forEach.call( elems_dark, function( elem ){
            elem.classList.remove( 'theme-dark' );
            elem.classList.add( 'theme-light' );
        });
        Array.prototype.forEach.call( document.getElementsByClassName('navbar-dark'), function( elem ){
            elem.classList.add('navbar-light');
            elem.classList.remove('navbar-dark');
        });
        Array.prototype.forEach.call( document.getElementsByTagName('hr'), function( elem ){
            elem.classList.add('bg-dark');
            elem.classList.remove('bg-white');
        });
        Array.prototype.forEach.call( document.querySelectorAll('nav .dropdown-item'), function( elem ){
            elem.classList.remove('text-white');
        });
        singleFormBtn.classList.remove('btn-dark');
        singleFormBtn.classList.add('btn-light', 'btn-outline-dark');
        setCookie('theme', 'light', 30);
    }
});

( function ( document, window, index )
{
    // feature detection for drag&drop upload
    var isAdvancedUpload = function()
    {
        var div = document.createElement( 'div' );
        return ( ( 'draggable' in div ) || ( 'ondragstart' in div && 'ondrop' in div ) ) && 'FormData' in window && 'FileReader' in window;
    }();

    // applying the effect for every form
    var forms = document.querySelectorAll( '.box' );
    Array.prototype.forEach.call( forms, function( form )
    {
        var input		 = form.querySelector( 'input[type="file"]' ),
            label		 = form.querySelector( 'label' ),
            errorMsg	 = form.querySelector( '.box__error span' ),
            restart		 = form.querySelectorAll( '.box__restart' ),
            droppedFiles = false,
            showFiles	 = function( files )
            {
                label.textContent = files.length > 1 ? ( input.getAttribute( 'data-multiple-caption' ) || '' ).replace( '{count}', files.length ) : files[ 0 ].name;
            },
            triggerFormSubmit = function()
            {
                var event = document.createEvent( 'HTMLEvents' );
                event.initEvent( 'submit', true, false );
                form.dispatchEvent( event );
            };

        // automatically submit the form on file select
        input.addEventListener( 'change', function( e )
        {
            if ( e.target.files.length != '' )
            {
                showFiles( e.target.files );

                triggerFormSubmit();
            }
        });

        // drag&drop files if the feature is available
        if( isAdvancedUpload )
        {
            form.classList.add( 'has-advanced-upload' ); // letting the CSS part to know drag&drop is supported by the browser

            [ 'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop' ].forEach( function( event )
            {
                form.addEventListener( event, function( e )
                {
                    // preventing the unwanted behaviour
                    e.preventDefault();
                    e.stopPropagation();
                });
            });
            [ 'dragover', 'dragenter' ].forEach( function( event )
            {
                form.addEventListener( event, function()
                {
                    form.classList.add( 'is-dragover' );
                });
            });
            [ 'dragleave', 'dragend', 'drop' ].forEach( function( event )
            {
                form.addEventListener( event, function()
                {
                    form.classList.remove( 'is-dragover' );
                });
            });
            form.addEventListener( 'drop', function( e )
            {
                droppedFiles = e.dataTransfer.files; // the files that were dropped
                showFiles( droppedFiles );

                triggerFormSubmit();
            });
        }
        
        // if the form was submitted
        form.addEventListener( 'submit', function( e )
        {
            var identity = form.getAttribute( 'id' );
            // preventing the duplicate submissions if the current one is in progress
            if( form.classList.contains( 'is-uploading' ) ) return false;

            form.classList.add( 'is-uploading' );
            form.classList.remove( 'is-error', 'is-success' );

            if( isAdvancedUpload ) // ajax file upload for modern browsers
            {
                e.preventDefault();

                // creating new form
                var ajaxData = new FormData();
                if ( input.files.length != 0 )
                {
                    Array.prototype.forEach.call( input.files, function( file )
                    {
                        ajaxData.append( input.getAttribute( 'name' ), file );
                    });
                }
                // gathering the form data
                if( droppedFiles )
                {
                    Array.prototype.forEach.call( droppedFiles, function( file )
                    {
                        ajaxData.append( input.getAttribute( 'name' ), file );
                    });
                }
                if( identity != 'newUserDataForm' )
                {
                    var missingValuesOption = document.querySelector( '#fileForm input[name = "missingValuesOption"]:checked' );
                    ajaxData.append( missingValuesOption.getAttribute( 'name' ), missingValuesOption.getAttribute( 'id' ) );
                }
                
                // ajax request
                var ajax = new XMLHttpRequest();
                ajax.open( form.getAttribute( 'method' ), form.getAttribute( 'action' ), true );
                ajax.responseType = "blob";

                ajax.onload = function()
                {
                    form.classList.remove( 'is-uploading' );

                    if( ajax.status >= 200 && ajax.status < 400 )
                    {
                        if( identity == 'newUserDataForm' )
                        {
                            var data = JSON.parse( ajax.responseText );
							form.classList.add( data.success == true ? 'is-success' : 'is-error' );
							if( !data.success ) errorMsg.textContent = JSON.parse(ajax.responseText).error;
                        }
                        else
                        {
                            var filename = "";
                            var disposition = ajax.getResponseHeader('Content-Disposition');
                            if (disposition && disposition.indexOf('attachment') !== -1)
                            {
                                var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                                var matches = filenameRegex.exec(disposition);
                                if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');
                            }
                            
                            var type = ajax.getResponseHeader('Content-Type');
                            
                            var blob = new Blob([this.response], { type: type });

                            if (typeof window.navigator.msSaveBlob !== 'undefined')
                            {
                                // IE workaround for "HTML7007: One or more blob URLs were revoked by closing the blob for which they were created. These URLs will no longer resolve as the data backing the URL has been freed."
                                window.navigator.msSaveBlob(blob, filename);
                            }
                            else
                            {
                                var URL = window.URL || window.webkitURL;
                                var downloadUrl = URL.createObjectURL(blob);

                                if ( filename )
                                {
                                    // use HTML5 a[download] attribute to specify filename
                                    var a = document.createElement("a");
                                    // safari doesn't support this yet
                                    if (typeof a.download === 'undefined')
                                    {
                                        window.location = downloadUrl;
                                    }
                                    else
                                    {
                                        a.href = downloadUrl;
                                        a.target = '_blank';
                                        a.download = filename;
                                        document.body.appendChild(a);
                                        a.click();
                                    }
                                }
                                else
                                {
                                    window.location = downloadUrl;
                                }
                                setTimeout(function() { URL.revokeObjectURL(downloadUrl); }, 100); // cleanup
                            }
                            form.classList.add( 'is-success' );
                        }
                    }
                    else
                    {
                        form.classList.add( 'is-error' );
                        errorMsg.textContent = JSON.parse(ajax.responseText).error;
                    }
                };

                ajax.onerror = function()
                {
                    form.classList.remove( 'is-uploading' );
                    alert( 'Error. Please, try again!' );
                };

                ajax.send( ajaxData );
            }
            else // fallback Ajax solution upload for older browsers
            {
                var iframeName	= 'uploadiframe' + new Date().getTime(),
                    iframe		= document.createElement( 'iframe' );
                    $iframe		= $( '<iframe name="' + iframeName + '" style="display: none;"></iframe>' );

                iframe.setAttribute( 'name', iframeName );
                iframe.style.display = 'none';

                document.body.appendChild( iframe );
                form.setAttribute( 'target', iframeName );

                iframe.addEventListener( 'load', function()
                {
                    form.classList.remove( 'is-uploading' );
                    var data = iframe.contentDocument.body.innerHTML || iframe.contentWindow.document.body.innerHTML;
                    
                    form.classList.add( data.success ? 'is-success' : 'is-error' );
                    form.removeAttribute( 'target' );
                    if( !data.success ) errorMsg.textContent = data.error;
                    iframe.parentNode.removeChild( iframe );
                });
            }
        });

        // restart the form if has a state of error/success
        Array.prototype.forEach.call( restart, function( entry )
        {
            entry.addEventListener( 'click', function( e )
            {
                e.preventDefault();
                form.classList.remove( 'is-success', 'is-error' );
                // form.reset();
                input.click();
            });
        });

        // Firefox focus bug fix for file input
        input.addEventListener( 'focus', function(){ input.classList.add( 'has-focus' ); });
        input.addEventListener( 'blur', function(){ input.classList.remove( 'has-focus' ); });
    });

    // single entry form request
    var singleEntryForm = document.querySelector( '#singleEntryForm' );
    singleEntryForm.addEventListener( 'submit', function( e )
    {
        e.preventDefault();
        var alertElem = singleEntryForm.querySelectorAll( '.alert' );
        Array.prototype.forEach.call( alertElem, function( node ){
            node.remove();
        });
        var btnSubmit = singleEntryForm.querySelector( 'button[type="submit"]' );
        var input = singleEntryForm.querySelectorAll( 'input' );
        var select = singleEntryForm.querySelectorAll( 'select' );
        
        btnSubmit.disabled = true;
        btnSubmit.textContent = "Analysing...";

        // ajax request
        var ajaxData = new FormData( singleEntryForm );
        var ajax = new XMLHttpRequest();
        
        ajax.open( singleEntryForm.getAttribute( 'method' ), singleEntryForm.getAttribute( 'action' ), true );
        ajax.onload = function()
        {
            if( ajax.status >= 200 && ajax.status < 400 )
            {
                var data = JSON.parse(ajax.responseText);

                if ( data.status === 'error' )
                {
                    // Validation Errors Here
                    // console.log( 'error' );
                    btnSubmit.insertAdjacentHTML( 
                        'beforebegin',
                        '<div class="alert alert-danger mt-2 font-weight-bold">'+ data.error +'</div>'
                    );
                    singleEntryForm.reset();
                }
                else
                {
                    // alert('success');
                    var insightsArea = document.getElementById( 'singleRecordInsights' );
                    insightsArea.classList.remove('d-none');

                    var tableData = '<table class="table table-sm text-center"><thead class="thead-dark"><tr>';
                    data.features.forEach( element => tableData += ('<th>'+element+'</th>') );
                    tableData += '</tr></thead><tbody><tr>';
                    data.values.forEach( element => tableData += ('<td>'+element+'</td>') );
                    tableData += '</tr></tbody></table>';

                    var appStatus = '<div class="alert alert-'+ data.resType+' mt-3 font-weight-bold w-100">The Entered Loan Application looks '+ data.category +'</div>';

                    insightsArea.querySelector( '.card-body div.card-text' ).innerHTML = tableData;
                    insightsArea.querySelector( '.card-body p.card-text' ).innerHTML = appStatus;

                    insightsArea.querySelector( '.col-12.col-lg-4 img' ).src = 'data:image/png;base64,' + data.imgUrl;

                    singleEntryForm.reset();
                }
            }
            else alert( 'Something went Wrong. Please, contact the webmaster!' );

            btnSubmit.disabled = false;
            btnSubmit.textContent = "Analyse Details";
        };
        ajax.onerror = function()
        {
            alert( 'Something went wrong. Please, try again!' );
        };
        ajax.send( ajaxData );
    });
}( document, window, 0 ));