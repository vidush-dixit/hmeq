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
            showFiles( e.target.files );

            triggerFormSubmit();		
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
            // preventing the duplicate submissions if the current one is in progress
            if( form.classList.contains( 'is-uploading' ) ) return false;

            form.classList.add( 'is-uploading' );
            form.classList.remove( 'is-error', 'is-success' );

            if( isAdvancedUpload ) // ajax file upload for modern browsers
            {
                e.preventDefault();

                // creating new form
                var ajaxData = new FormData();
                // gathering the form data
                if( droppedFiles )
                {
                    Array.prototype.forEach.call( droppedFiles, function( file )
                    {
                        ajaxData.append( input.getAttribute( 'name' ), file );
                    });
                }
                
                // ajax request
                var ajax = new XMLHttpRequest();
                ajax.open( form.getAttribute( 'method' ), form.getAttribute( 'action' ), true );
                // ajax.responseType = "blob";

                ajax.onload = function()
                {
                    form.classList.remove( 'is-uploading' );

                    if( ajax.status >= 200 && ajax.status < 400 )
                    {
                        if( ajax.getResponseHeader('Content-Type') != 'application/json' )
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

                                if (filename)
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
                        else
                        {
                            form.classList.add( 'is-error' );
							errorMsg.textContent = JSON.parse(ajax.responseText).error;
                        }
                    }
                    else alert( 'Error. Please, contact the webmaster!' );
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
                    var data = JSON.parse( iframe.contentDocument.body.innerHTML );
                    form.classList.add( data.success == true ? 'is-success' : 'is-error' );
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
                    // alert('error');
                    console.log( 'error' );
                }
                else
                {
                    // alert('success');
                    btnSubmit.insertAdjacentHTML( 
                        'beforebegin',
                        '<div class="alert alert-'+ data.resType+' mt-2 font-weight-bold">The Entered Loan Application looks  '+ data.result +'</div>'
                    );
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