/**
 * JsonRpc Adapter (using ajax)
 * @static 
 */
WireIt.WiringEditor.adapters.JsonRpc = {
	
	config: {
		url: '/xml/generate'
	},
	
	init: function() {
		//YAHOO.util.Connect.setDefaultPostHeader('application/json');
		 YAHOO.util.Connect.initHeader("Content-Type", "application/x-www-form-urlencoded");

	},
	
	saveWiring: function(val, callbacks) {
		this._sendJsonRpcRequest("saveWiring", val, callbacks);
	},
	
	deleteWiring: function(val, callbacks) {
		this._sendJsonRpcRequest("deleteWiring", val, callbacks);
	},
	
	listWirings: function(val, callbacks) {
		//this._sendJsonRpcRequest("listWirings", val, callbacks);
	},
	
	// private method to send a json-rpc request using ajax
	_sendJsonRpcRequest: function(method, value, callbacks) {
		//var postData = YAHOO.lang.JSON.stringify({"id":(this._requestId++),"method":method,"params":value,"version":"json-rpc-2.0"});
		//
		var recName = value["name"];
		var wireData = YAHOO.lang.JSON.parse(value["working"]);
		var postData = "json_data=" + encodeURIComponent(YAHOO.lang.JSON.stringify(wireData)) + "&name=" + encodeURIComponent(recName);

		YAHOO.util.Connect.asyncRequest('POST', this.config.url, {

			success: function(o) {
				var s = o.responseText,
					 r = YAHOO.lang.JSON.parse(s);
			 	callbacks.success.call(callbacks.scope, r.result);
			},
			failure: function() {
				var r = null;
				callbacks.failure.call(callbacks.scope, r);
			}
		},postData);
	},
	_requestId: 1
};
