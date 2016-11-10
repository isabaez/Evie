"use strict";
var request = require('request');

var url = 'https://evie.herokuapp.com/listCheck';

request.get(url, function(err, response, body) {
  console.log('here');
 if (err) {
   console.log("Error. Couldn't load '%s' Error: %s", url, err);
   process.exit(1);
 } else {
   if (Math.floor(response.statusCode / 100) === 2) {
     console.log("Success. Loaded: '%s' Response: %s", url, body);
     process.exit(0);
   } else {
     console.log("Error. Loaded: '%s' Status: %s Response: %s",
         url, response.statusCode, body);
     process.exit(1);
   }
 }
});