/* render strings */

function getParam(param) {
  let paramString = window.location.href.split('?')[1];
  let queryString = new URLSearchParams(paramString);
  for (let pair of queryString.entries()) {
    if (pair[0] == param)
      return pair[1];
  }
}

function getLang() {
  if (navigator.languages != undefined) 
    return navigator.languages[0]; 
  return navigator.language;
}

var lang = getLang().split('-')[0];

var param_lang = getParam('lang');
if (param_lang)
  lang = param_lang;

if (lang != 'es' && lang != 'en')
  lang = 'en';
  
var string_files = ['menu', 'teaching', 'home', 'datasets'];
var strings = {}

if (getParam('render') == "1") { 
	for (i = 0; i < string_files.length; i++) {
	  xhttp = new XMLHttpRequest();
	  xhttp.onreadystatechange = function() {
	  if (this.readyState == 4) {
	    if (this.status == 200) {strings = Object.assign({}, strings, JSON.parse(this.responseText));}
	    if (this.status == 404) {console.log("String file " + string_files[i] + "not found");}
	    }
	  }
	  var file = "../strings/" + string_files[i] + "_" + lang + ".json";
	  xhttp.open("GET", file, false);
	  xhttp.send();    
	}
}
  
function includeHTML() {
  var z, i, elmnt, file, xhttp;
  /* Loop through a collection of all HTML elements: */
  z = document.getElementsByTagName("*");
  for (i = 0; i < z.length; i++) {
    elmnt = z[i];
    /*search for elements with a certain atrribute:*/
    file = elmnt.getAttribute("w3-include-html");
    if (file) {
      /* Make an HTTP request using the attribute value as the file name: */
      xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
          if (this.status == 200) {elmnt.innerHTML = this.responseText;}
          if (this.status == 404) {elmnt.innerHTML = "Page not found.";}
          /* Remove the attribute, and call this function once more: */
          elmnt.removeAttribute("w3-include-html");
          includeHTML();
        }
      }
      xhttp.open("GET", file, false);
      xhttp.send();
      /* Exit the function: */
      return;
    }
  }
}

function setStrings() {
  var z, i, elmnt, file, xhttp;
  /* Loop through a collection of all HTML elements: */
  z = document.getElementsByTagName("*");
  for (i = 0; i < z.length; i++) {
    elmnt = z[i];
    /*search for elements with a certain atrribute:*/
    string = elmnt.getAttribute("w3-string-html");
    if (string) {
      console.log(string);
      if (string in strings) {
        elmnt.innerHTML = strings[string];
      	elmnt.removeAttribute("w3-include-html");
      	includeHTML();
      }
        
    }
  }
}

function render() {
  if (getParam('render') == "1") { 
    console.log("render");
    includeHTML();
    setStrings();
  }
}
