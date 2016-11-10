var express = require('express');
var router = express.Router();
var User = require('../models/models').User;
var Groups = require('../models/models').Group;
var List = require('../models/models').List;
var Event = require('../models/models').Event;
var EventMaster = require('../models/models').EventMaster;

var twilio = require('twilio')(process.env.ACCOUNT_SID, process.env.AUTH_TOKEN);

function randomCode() {
  var min = 1000;
  var max = 9999;
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

router.get('/listCheck', function(req, res, next) {
	var date = new Date();
	List.find({}, function(err, lists) {
		lists.forEach(function(list) {
			if (list.timeLimit <= date && list.status === "Open") {
				if (err) {
					console.log(err)
				} else {
					var update = {
						status: "Closed"
					}
					List.findByIdAndUpdate(list._id, update, function(err, list) {
						if (err) {
							console.log(err)
						} else {
							Groups.findById(list.parentGroup).populate('users').exec(function(err, group) {
								if (err) console.log(err)
								else {
									group.users.forEach(function(user) {
										twilio.sendMessage({
											to: user.phoneNum,
											from: process.env.FROM_PHONE,
											body: "Voting on " + list.name + " has closed, time limit has been reached! View your results now!"
										}, function(err, data) {
											console.log(err);
											console.log(data);
										})
									})
								}
							})
						}
					})
				}
			}
		})
		res.send(200);
	})
})

router.get('/verify/:id', function(req, res, next) {
	User.findById(req.params.id, function(err, user) {
		if (!user) {
			res.redirect('/login')
		} else {
			user.registrationCode = randomCode().toString();
			user.save(function(err) {
				if (err) {
					console.log(err);
					return;
				}
			});
			twilio.sendMessage({
	        to: "+1" + user.phoneNum,
	        from: process.env.FROM_PHONE,
	        body: "Your 4-digit Code is: " + user.registrationCode
	      	}, function(err, resp) {
	        	if (err) {
	          		console.log(err);
	          		return;
	        	}
	      	})
			res.render('verify', {
				user: user
			})
		}
	})
})

router.post('/verify/:id', function(req, res, next) {
	User.findById(req.params.id, function(err, user) {
		if (user.registrationCode === req.body.code) {
			var update = {
				verified: true
			}
			User.findByIdAndUpdate(req.params.id, update, function(err, user) {
				if (err) console.log(err)
				else {
					res.redirect('/login');
				}
			})
		} else {
			res.render('verify', {
				error: "Incorrect verification code"
		})
	}
	})
})


/* GET home page. */
router.use(function(req, res, next) {
	if (!req.user) {
		res.redirect('/login')
	} else {
		User.findById(req.user.id, function(err, user) {
			if (user.verified === false) {
				res.redirect('/verify/' + user._id)
			} else {
				return next();
			}
		})
	}
})

router.get('/', function(req, res, next) {
	res.redirect('/groups');
})

router.get('/groups', function(req, res, next) {
	User.findById(req.user.id).populate('groups').exec(function(err, user) {
		res.render('groups', {
			groups: user.groups
		});
	})
});

router.post('/groups', function(req, res, next) {
	var g = new Groups({
		users: [req.user.id],
		lists: [],
		name: req.body.name,
		description: req.body.description,
		searchLocation: req.body.location
	})
	g.save(function(err, group) {
		if (err) {
			console.log(err)
		} else {
			var update = {
				$push: {groups: group._id}
			}
			User.findByIdAndUpdate(req.user.id, update, function(err, user) {
				if (err) {
					console.log(err)
				} else {
					res.redirect('/groups')
				}
			})
		}
	})
});

router.get('/groups/:gid', function(req, res, next) {
	Groups.findById(req.params.gid).populate('users').exec(function(err, group) {
		List.find( {parentGroup: req.params.gid} ).exec(function(err, lists) {
			var arr = [];
			var arr2 = [];
			lists.forEach(function(list) {
				if(list.status === 'Open') {
					arr.push(list)
				} else if (list.status === 'Closed'){
					arr2.push(list)
				}
			})
			res.render('singleGroup', {
				users: group.users,
				lists: arr,
				closed: arr2,
				name: group.name,
				description: group.description
			});
		})
	})
});

router.post('/groups/:gid', function(req, res, next) {
	if(req.body.username) {
		var update = {
			$push: {groups: req.params.gid}
		}
		User.findOneAndUpdate( {username: req.body.username }, update, function(err, user) {
			if (err) {
				console.log(err)
				return res.redirect('/groups/' + req.params.gid)
			} if (!user) {
				return res.redirect('/groups/' + req.params.gid)
			}
			else {
				var updateGroup = {
					$push: {users: user._id}
				}
				Groups.findByIdAndUpdate(req.params.gid, updateGroup, function(err, group) {
					if (err) {
						console.log(err)
					} else {
						res.redirect('/groups/' + req.params.gid)
					}
				})
			}
		})
	} else {
		var l = new List({
			events: [],
			parentGroup: req.params.gid,
			parentUser: req.user.id,
			name: req.body.name,
			fromDate: req.body.fromDate,
			toDate: req.body.toDate,
			searchLocation: req.body.searchLocation,
			description: req.body.description,
			status: "Open",
			usersCompleted: [],
			timeLimit: req.body.timeLimit
		});
		l.save(function(err, list) {
			if (err) {
				console.log(err)
			} else {
				var arr = req.body.select;
				if(typeof arr === 'string'){
					arr = [arr];
				}
				if (arr.indexOf('nightlife') !== -1) {
					EventMaster.find({eventType: 'nightlife'}, function(err, events) {
						events.forEach(function(event) {
							var e = new Event({
								event: event._id,
								tally: [],
								parentList: list._id
							})
							e.save(function(err, event) {
								if (err) {
									console.log(err)
								} else {
									var update = {
										$push: {events: event._id}
									}
									List.findByIdAndUpdate(list._id, update, function(err, list) {
										if (err) {
											console.log(err)
										}
									})
								}
							})
						})
					})
					arr.splice(arr.indexOf('nightlife'), 1);
				}
				if (arr.indexOf('historic') !== -1) {
					EventMaster.find({eventType: 'historic'}, function(err, events) {
						console.log(events);
						events.forEach(function(event) {
							var e = new Event({
								event: event._id,
								tally: [],
								parentList: list._id
							})
							e.save(function(err, event) {
								if (err) {
									console.log(err)
								} else {
									var update = {
										$push: {events: event._id}
									}
									List.findByIdAndUpdate(list._id, update, function(err, list) {
										if (err) {
											console.log(err)
										}
									})
								}
							})
						})
					})
					arr.splice(arr.indexOf('historic'), 1);
				}
				EventMaster.find({ date: { $gt: req.body.fromDate, $lt: req.body.toDate }, eventType: { $in: arr }}, function(err, events) {
					events.forEach(function(event) {
						var e = new Event({
							event: event._id,
							tally: [],
							parentList: list._id
						})
						e.save(function(err, event) {
							if (err) {
								console.log(err)
							} else {
								var update = {
									$push: {events: event._id}
								}
								List.findByIdAndUpdate(list._id, update, function(err, list) {
									if (err) {
										console.log(err)
									}
								})
							}
						})
					})
				})
				res.redirect('/groups/' + req.params.gid)
			}
		})
	}
});

router.get('/eventLoad/:lid', function(req, res, next) {
	var list = req.session.votes.find(function(list) {
		return list._id === req.params.lid;
	});
	if (!list)
		res.redirect('/loadSession/' + req.params.lid)
	else if (list.events.length === 0) {
		var update = {
			$push: {usersCompleted: req.user.id}
		}
		List.findByIdAndUpdate(req.params.lid, update).populate('parentGroup').exec(function(err, list) {
			if (err) console.log(err)
			else if (list.parentGroup.users.length-1 === list.usersCompleted.length) {
				res.redirect('/message/' + list._id);
			}
			else {
				res.redirect('/results/' + list._id)
			}
		})
	}
	else {
		res.redirect('/eventVote/' + list.events[list.events.length - 1])
	}
});

router.get('/loadSession/:lid', function(req, res, next) {
	List.findById(req.params.lid, function(err, list) {
		if (err) {
			console.log(err)
		} else {
			req.session.votes.push({_id: req.params.lid, events: list.events})
			res.redirect('/eventLoad/' + req.params.lid)
		}
	})
})

router.get('/eventVote/:eid', function(req, res, next) {
	Event.findById(req.params.eid).populate('event').exec(function(err, event) {
		List.findById(event.parentList, function(err, list) {
			if (err) console.log(err)
			else {
				res.render('eventVote', {
					title: event.event.title,
					description: event.event.description,
					location: event.event.location,
					date: event.event.date,
					startTime: event.event.startTime,
					price: event.event.price,
					imageUri: event.event.imageUri,
					gid: list.parentGroup
				})
			}
		})
	})
})

router.post('/eventVote/:eid', function(req, res, next) {
	Event.findById(req.params.eid, function(err, event) {
		if(err) console.log(err);
		else {
			var list = req.session.votes.find(function(list) {
			return list._id === "" + event.parentList
		})
		list.events.pop();
			if (req.body.choice === "Yes") {
				var update = { $push: { tally: req.user.id } };
				Event.findByIdAndUpdate(req.params.eid,update,function(err, event){
					if(err) console.log(err)
				})
			}
			res.redirect('/eventLoad/' + event.parentList);
		}
	})
})

router.get('/results/:lid', function(req, res, next) {
		Event.find({parentList: req.params.lid}).populate('event parentList').exec(function(err, events){
		if (err) console.log(err)
		else {
			var display = "none";
				if(events[0].parentList.status === "Closed" && "" + events[0].parentList.parentUser === req.user.id){
				display = "block";
				}
			var sortedEvents = events.sort(function(a, b) {
				return b.tally.length - a.tally.length
			})
			res.render('results', {
				results: sortedEvents,
				_id: events[0].parentList._id,
				display: display
			})
		}
		})
})

router.get('/actNow/:lid', function(req, res, next){
		Event.find({parentList: req.params.lid}).populate('event parentList').exec(function(err, events){
			if(err) console.log(err)
			else{
				var winners = [];
				var sortedEvents = events.sort(function(a, b) {
				return b.tally.length - a.tally.length
				})
				var high = sortedEvents[0].tally.length;
				sortedEvents.forEach(function(event, index){
					if(event.tally.length === high){
						winners.push(event);
					}
				})
				res.render('actNow', {
					winners: winners,
					results: sortedEvents
				})
			}
		})

})

router.get('/message/:lid', function(req, res, next) {
	var update = {
		status: "Closed"
	}
	List.findByIdAndUpdate(req.params.lid, update, function(err, list) {
		if (err) {
			console.log(err)
		} else {
			Groups.findById(list.parentGroup).populate('users').exec(function(err, group) {
				if (err) console.log(err)
				else {
					group.users.forEach(function(user) {
						twilio.sendMessage({
							to: user.phoneNum,
							from: process.env.FROM_PHONE,
							body: "Voting on " + list.name + " has completed! View your results now!"
						})
					})
					res.redirect('/results/' + list._id)
				}
			})
		}
	})
})

router.get('/confirm/:eid', function(req, res, next) {
	Event.findById(req.params.eid).populate('event').exec(function(err, event) {
		var update = {
			status: "Complete"
		}
		List.findByIdAndUpdate(event.parentList, update, function(err, list) {
			if (err) console.log(err)
			else {
				var date;
				if (event.event.eventType === "nightlife" || event.event.eventType === "historic") {
					date = list.fromDate
				} else {
					date = event.event.date
				}
				event.tally.forEach(function(userId) {
					User.findById(userId, function(err, user) {
						if(err) console.log(err);
						else {
							twilio.sendMessage({
								to: user.phoneNum,
								from: process.env.FROM_PHONE,
								body: "Your event " + event.event.title + " has been confirmed for " + date + " at " + event.event.location + " at " + event.event.startTime
							})
						}
					})
				})
			}
			res.redirect('/groups/' + list.parentGroup);
		})
	})
})




module.exports = router;
