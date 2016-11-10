var mongoose = require('mongoose');

var userSchema = mongoose.Schema({
	username: {
		type: String,
		required: true
	},
	password: {
		type: String,
		required: true
	},
	phoneNum: {
		type: String,
		required: true
	},
	groups: [{
		type: mongoose.Schema.ObjectId,
		ref: 'Group',
		default: []
	}],
	registrationCode: String,
	verified: Boolean
});

var eventServantSchema = mongoose.Schema({
	event: {
		type: mongoose.Schema.ObjectId,
		ref: 'EventMaster'
	},
	tally: [{
			type: mongoose.Schema.ObjectId,
			ref: 'User'
	}],
	parentList: {
		type: mongoose.Schema.ObjectId,
		ref: 'List'
	}
});

var groupSchema = mongoose.Schema({
	users: [{
		type: mongoose.Schema.ObjectId,
		ref: 'User'
	}],
	lists: [{
		type: mongoose.Schema.ObjectId,
		ref: "List"
	}],
	name: String,
	description: String
});

var listSchema = mongoose.Schema({
	events: [{
		type: mongoose.Schema.ObjectId,
		ref: 'Event'
	}],
	parentGroup: {
		type: mongoose.Schema.ObjectId,
		ref: 'Group'
	},
	parentUser: {
		type: mongoose.Schema.ObjectId,
		ref: 'User'
	},
	description: String,
	name: String,
	fromDate: Date,
	toDate: Date,
	searchLocation: String,
	status: String,
	usersCompleted: Array,
	timeLimit: Date
})

var eventMasterSchema = mongoose.Schema({
	title: String,
	location: String,
	description: String,
	eventType: String,
	date: Date,
	startTime: String,
	price: String,
	imageUri: String
})

module.exports = {
	User: mongoose.model('User', userSchema),
	Event: mongoose.model('Event', eventServantSchema),
	EventMaster: mongoose.model('EventMaster', eventMasterSchema),
	Group: mongoose.model('Group', groupSchema),
	List: mongoose.model('List', listSchema)
}