function get_XmlHttp() {
  // create the variable that will contain the instance of the XMLHttpRequest object (initially with null value)
  var xmlHttp = null;

  if(window.XMLHttpRequest) {		// for Forefox, IE7+, Opera, Safari, ...
    xmlHttp = new XMLHttpRequest();
  }
  else if(window.ActiveXObject) {	// for Internet Explorer 5 or 6
    xmlHttp = new ActiveXObject("Microsoft.XMLHTTP");
  }

  return xmlHttp;
}


function showComments (post_id,user_id){
	//document.getElementById(post_id).innerHTML=post_id;
	var content=document.getElementById("comment"+post_id).value;
	
	 var request =  get_XmlHttp();		// call the function for the XMLHttpRequest instance
  var  url = 'wp-content/themes/detube/showComments.php?post_id='+post_id+'&user_id='+user_id+'&content='+content;
  
  request.open("GET", url, true);			// define the request
  request.send(null);		// sends data

  // Check request status
  // If the response is received completely, will be transferred to the HTML tag with tagID
  request.onreadystatechange = function() {
    if (request.readyState == 4) {
	  //alert (request.responseText);
	  document.getElementById(post_id).innerHTML=request.responseText;
    }
  }
	
}