var objUpdate = function(obj1,obj2){
    if(typeof obj2 === 'object' && typeof obj1 !== 'object'){
        //for now
        obj1 = {};
    } 
    for(var k in obj2){
        if(typeof obj2[k] === 'object'){
            if(obj1[k] && typeof obj1[k] === 'object'){
                objUpdate(obj1[k],obj2[k]);
            }else{
                obj1[k] = obj2[k];
            }
        }else if(typeof obj2[k] === 'array'){
            if(obj1[k] && typeof obj1[k] === 'array'){
                obj1[k] = obj1[k].concat(obj2[k]);
            }else{
                obj1[k] = obj2[k];
            }
        }else{
            obj1[k] = obj2[k];
        }
    }
};

/*
Object.prototype.smDeltaUpdate = function(obj){
    objUpdate(this,obj);
}
*/
/*
Object.prototype.sm_update = function(obj){
    objUpdate(this,obj);
};
*/
/*
ko.extenders.objUpdate = function(target, option){
    if(option){
        target.subscribe(function(new_value){
            console.log(new_value);
            console.log(current_value);
            console.log(this);
            console.log(target());
            window.debug = target;
            if(0){
                return;
            }
            var curr = target();
            if(typeof curr !== "object"){
                target(new_value);
                return;
            }
            objUpdate(curr,new_value);
            target(curr);
            return target;
        });
    }
};
*/

function CLHelperViewModel() {
    var viewModel = this;
    this.meta = ko.observable({})
    this.posts = ko.observableArray([]);
    this.user = ko.observable("");
    this.passwd = ko.observable("");
    this.userSelect = ko.observable("New User");
    this.status = ko.observable("Not Started");
    this.last_updated = new Date(0);
    this.authInputOpen = ko.observable(false);
    this.authCode = ko.observable("");
    this.period = ko.observable(6);
    this.periodOptions = ko.observableArray([
        {
            name: "4 minutes",
            value: 4
        },
        {
            name: "6 minutes",
            value: 6
        },
        {
            name: "8 minutes",
            value: 8
        },
        {
            name: "10 minutes",
            value: 10
        },
        {
            name: "12 minutes",
            value: 12
        },
    ]);
    this.available_users = ko.observableArray([]);
    this.selectedUsers = ko.observableArray([]);

    this.available_google_users = ko.observableArray([]);
    this.selectedGoogleAccount = ko.observable('');

    this.alertData = ko.observable({
        danger: {
            title: '',
            body: '',
            shown: false
        },
        success: {
            title: '',
            body: '',
            shown: false
        }
    });//.extend({objUpdate: true});
    this.alerts = {
        danger: $("#dangerAlert"),
        success: $("#successAlert")
    }

    /*
    this.dangerTitle = ko.observable("");
    this.dangerBody = ko.observable("");
    this.showDanger = ko.observable(false);
    this.dangerAlert = $("#dangerAlert");

    this.successTitle = ko.observable("");
    this.successBody = ko.observable("");
    this.showSuccess = ko.observable(false);
    this.successAlert = $("#successAlert");
    */

    this.installProgress = ko.observable(0);
    this.installModalTitle = ko.observable("");
    this.installModalBody = ko.observable("");
    this.installModal = $("#installProgress");


    this.addUser = function(){
        var self = this;
        googleAccount = self.user().endsWith("@gmail.com") ? self.user() : self.selectedGoogleAccount()[0];
        payload = {
            'user': self.user(),
            'pw': self.passwd(),
            'google_account': googleAccount
        };
        $.ajax({
            url: '/add_account',
            method: 'POST',
            data: JSON.stringify(payload),
            success: function(resp){
                if(resp.status=='success'){
                    self.available_users.push(resp.account.user);
                    self.status("User Added Successfully");
                }else{
                    self.status(resp.status);
                }
                self.user("");
                self.passwd("");
            },
            contentType: 'application/json'
        });
    };

    this.deleteUsers = function(){
        var self = this;
        payload = {
            "accounts": self.selectedUsers()
        };
        $.ajax({
            url: "/delete_accounts",
            method: "POST",
            data: JSON.stringify(payload),
            success: function(resp){
                if(resp.status=='success'){
                    self.available_users(resp.available_accounts);
                    self.status("Account(s) Removed");
                }else{
                    self.status("Error removing account(s)");
                }
            },
            contentType: "application/json"
        })
    };

    this.start = function(){
        var self = this;
        payload = {
            'accounts':self.selectedUsers(),
            'period': self.period()
        };
        /*
        confirmed = true;
        if(self.userSelect()==='New User' && !self.user().endsWith("@gmail.com")){
            confirmed = confirm("Please note that using a non-gmail email address requires that you link your email account to the CL Helper gmail account. For assistance with this, please provide your email address to Sam via email (smurphy917@gmail.com). Please confirm this step has been completed prior to running CL Helper with this account.");
        }
        if(!confirmed){
            return;
        }
        */
        $.ajax({
            url: '/start',
            method: 'POST',
            data: JSON.stringify(payload),
            success: function(resp){
                self.status(resp.status);
            },
            contentType: 'application/json'
        });
        this.last_updated = new Date(0);
    };

    this.poller = function(){
        return {
            poll: function(time){
                var self = this
                $.get('/poll',function(resp){
                    console.log(resp)
                    if(resp.last_updated){
                        console.log(resp.last_updated);
                        console.log(viewModel.last_updated.valueOf());
                    }
                    if(resp.last_updated && parseFloat(resp.last_updated) > viewModel.last_updated.valueOf()){
                        viewModel.status(resp.status);
                        viewModel.posts(resp.posts.slice(0,200));
                        viewModel.last_updated = resp.last_updated;
                    }
                    if(resp.added_accounts){
                        for(var i in resp.added_accounts){
                            viewModel.available_users.push(resp.added_accounts[i]);
                        }
                        viewModel.status(resp.status)
                    }
                    if(resp.added_google_accounts){
                        for(var i in resp.added_google_accounts){
                            viewModel.available_google_users.push(resp.added_google_accounts[i]);
                        }
                        viewModel.status(resp.status)
                    }
                    if(resp.available_update){
                        viewModel.updateVersion = resp.available_update;
                        var alertData = viewModel.alertData();
                        objUpdate(alertData,{
                            success: {
                                title: 'New Version Available! ',
                                body: 'Click to install version ' + resp.available_update + 'and restart CL Helper.',
                                button: {
                                    enabled: true,
                                    text: 'Install & Update',
                                    target: viewModel.install
                                }
                            }
                        });
                        viewModel.alertData(alertData);
                        viewModel.alerts.success.slideDown();
                    }
                    setTimeout(function(){self.poll(time)},time*1000);
                });
            },
            start: function(){
                this.poll(10);
            }
        }
    };

    this.installPoller = function(){
        return {
            poll: function(time){
                var self = this;
                $.ajax({
                    url: '/install_poll',
                    method: 'GET',
                    success: function(resp){
                        viewModel.installProgress(resp.install_progress);
                        if(resp.install_progress<100){
                            setTimeout(function(){self.poll(time)},time*1000);
                        }
                    }
                });

            },
            start: function(){
                this.poll(0.5);
            }
        }
    }

    this.complete_auth = function(){
        var self = this;
        var auth_data = {
            "access_code": this.authCode()
        }
        $.ajax({
            method: "POST",
            url: "/complete_auth",
            data: auth_data,
            contentType: "application/json",
            success: function(resp){
                self.authInputOpen(false);
            }
        });
    };

    this.init = function(){
        var self = this;
        $.get("/users",function(resp){
            var curr = self.available_users();
            var curr_gmail = self.available_google_users();
            for(var i in resp.available_users){
                curr.push(resp.available_users[i]);
            }
            for(var i in resp.available_google_users){
                curr_gmail.push(resp.available_google_users[i]);
            }
            self.available_users(curr);
            self.available_google_users(curr_gmail);
        });
        $.ajax({
            url: '/meta',
            method: 'GET',
            success: function(resp){
                self.meta(resp);
            }
        });
        this.poller().start()
    };

    this.pause = function(){
        var self = this;
        $.get("/pause",function(resp){
            self.status = resp.status;
        })
    };

    this.resume = function(){
        var self = this;
        $.get("/resume",function(resp){
            self.status = resp.status;
        })
    };

    this.add_google_user = function(){
        var self = this;
        $.ajax({
            url: '/add_google_account',
            method: 'GET',
            success: function(resp){
                self.status(resp.status);
                self.dangerAlert.slideUp();
            }
        });
    };

    this.submit_logs = function(){
        var self = this;
        if(!self.available_google_users().length){
            self.status("Error Sending Logs");
            var alertData = self.alertData();
            objUpdate(alertData,{
                danger:{
                    title: "Error! ",
                    body: "Cannot submit logs. At least one Google account must be added to submit logs."
                }
            });
            self.alertData(alertData);
            /*
            self.alertData({
                danger:{
                    title: "Error! ",
                    body: "Cannot submit logs. At least one Google account must be added to submit logs."
                }
            });
            */
            /*
            self.dangerTitle("Error! ");
            self.dangerBody("Cannot submit logs. At least one Google account must be added to submit logs.");
            */
            self.alerts.danger.slideDown();
            return;
        }
        $.ajax({
            url: '/submit_logs',
            method: 'GET',
            success: function(resp){
                self.status(resp.status);
                self.dangerAlert.slideUp();
            },
            error: function(){
                self.status("Error Sending Logs");
                var alertData = self.alertData();
                objUpdate(alertData,{
                    danger: {
                        title: "Error! ",
                        body: "Cannot submit logs. Please restart CL Helper and try again. Contact author if issue persists."
                    }
                });
                /*
                self.alertData({
                    danger: {
                        title: "Error! ",
                        body: "Cannot submit logs. Please restart CL Helper and try again. Contact author if issue persists."
                    }
                });
                */
                self.alertData(alertData);
                /*
                self.dangerTitle("Error!");
                self.dangerBody("Cannot submit logs. Please restart CL Helper and try again. Contact author if issue persists.");
                */
                self.alerts.danger.slideDown();
            }
        });
    };

    this.install = function(){
        $.ajax({
            url: '/install_update',
            method: 'POST',
            contentType: 'application/json',
            success: function(resp){
                if(resp.installing){
                    viewModel.installModalTitle("Downloading and Installing version " + viewModel.updateVersion);
                    viewModel.installModalBody("CL Helper will restart when complete.");
                    viewModel.installProgress(0);
                    viewModel.installModal.modal('show');
                    viewModel.installPoller().start();
                }
            }
        });
    };

    this.init()
}

var viewModel = new CLHelperViewModel();
ko.applyBindings(viewModel);