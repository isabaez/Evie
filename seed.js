var mongoose = require('mongoose');
var EventMaster = require('./models/models').EventMaster;
mongoose.connect(process.env.MONGODB_URI);

var events = require('./events.json');

events.forEach(function(event) {
	var e = new EventMaster({
		title: event.title,
		location: event.location,
		description: event.description,
		eventType: event.eventType,
		date: new Date(event.date),
		startTime: event.startTime,
		endTime: event.endTime,
		imageUri: event.imageUri,
		price: event.price
	})
	e.save(function(err, product) {
		if (err) {
			console.log(err);
		}
		console.log('saved to MongoDB')
	})
})