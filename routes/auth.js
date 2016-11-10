var express = require('express');
var router = express.Router();
var User = require('../models/models').User;

function randomCode() {
  var min = 1000;
  var max = 9999;
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

module.exports = function(passport) {

	//GET registration page
	router.get('/register', function(req, res) {
	    if (req.isAuthenticated()) {
	      res.redirect('/');
	    }
	    else {
	      res.render('register');
	    }
  	});

	// Password Validation
	var validateReq = function(userData) {
		return (userData.password === userData.passwordRepeat);
	};

	//POST registration page
  router.post('/register', function(req, res) {
    if (!validateReq(req.body)) {
      return res.render('register', {
        error: "Passwords don't match."
      });
    }
    var u = new User({
      username: req.body.username,
      password: req.body.password,
      phoneNum: req.body.phoneNum,
      registrationCode: randomCode().toString(),
      verified: false
    });
    u.save(function(err, user) {
      if (err) {
        console.log(err);
        res.status(500).redirect('/register');
        return;
      }
      res.redirect('/verify/' + u._id);
    });
  });

// GET Login page
  router.get('/login', function(req, res) {
    if (req.isAuthenticated()) {
      res.redirect('/')
    }
    res.render('login');
  });

  // POST Login page
  router.post('/login', passport.authenticate('local'), function(req, res) {
    if (req.isAuthenticated()) {
      if (!req.session.votes) {
        req.session.votes = [];
      }
      res.redirect('/');
    } else {
      console.log('here');
      res.render('login', {
        error: 'Username/password combination incorrect'
      })
    }
  });

  // GET Logout page
  router.get('/logout', function(req, res) {
    req.logout();
    res.redirect('/');
  });

  return router;
}