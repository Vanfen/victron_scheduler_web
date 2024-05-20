$(document).ready(function() {

    const currentUrl = window.location.href;
    if (currentUrl.toString().search("/main")) {
    }

    const form = document.getElementById("register_form");
    if (currentUrl.toString().search("/register") && form != null) {
        function handleForm(event) { event.preventDefault(); };
        form.addEventListener('submit', handleForm);
        const submitter = document.getElementById("register_button");
        submitter.addEventListener('click', function(){
            const formData = new FormData(form, submitter);
    
            const username = document.getElementById("username").value;
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;
            const confirm_password = document.getElementById("confirm_password").value;
            if (password != confirm_password) {
                const d = document.getElementById("confirm_password")
                d.classList.add("invalid");
                form.password_repeat.focus();
                return false;
            }
            $.ajax({
                method: "POST",
                url: "/auth/register",
                contentType: "application/json; charset=utf-8",
                dataType: 'json',
                data:  JSON.stringify({"username": username, "email": email, "password": password}),
                success: function (data) {
                    if (data["date_created"]) {
                        login(username, password);
                        window.location = '/main';
                    }
                },
                error: function (error) {
                    console.log(error.responseText);
                    alert("error" + error.responseText);
                }
            });
        })
    } else {
        if (currentUrl.toString().search("/login") < 0) {
            get_current_user()
        }
    }

    var user;

    async function get_current_user(){
        get_user = $.ajax({
            type: "GET",
            dataType: "json",
            url: "/auth/get_current_user",
            success: function (data) {
                username = document.getElementById("user_name_span");
                username.textContent = data["username"];
                return data;
            },
            error: function(error) {
                if (currentUrl.toString().search("/login") < 0) {
                    window.location = '/login';
                }
            }
        });
        get_user.done(function(user_result){
            user=user_result;
            if (user == null) {
                logout_user()
            }
        });
        await new Promise(r => setTimeout(r, 500));
    }

    const login_button = document.getElementById("login_button");
    if (login_button != null) {
        login_button.addEventListener('click', function(){
            const form = document.getElementById("login_form");
            function handleForm(event) { event.preventDefault(); } 
            form.addEventListener('submit', handleForm);
            const submitter = document.querySelector("button[value=Login]");
            const formData = new FormData(form, submitter);

            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;
            login(username, password);
        });
    }

    function login(username, password) {
        $.ajax({
            type: "POST",
            url: "/auth/token",
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            contentType: 'application/x-www-form-urlencoded; charset=utf-8',
            dataType: 'json',
            data:  {"username": username, "password": password},
            success: function (data) {
                if (data["access_token"]) {
                    window.location = '/main';
                }
            },
            error: function (error) {
                console.log(error.responseText);
                alert("error" + error.responseText);
            }
        });
    }

    // Make the API call here to parse all the latest data to notify the user about:
    // EX: Updated the victron scheduler at 00:00:00 dd-mm-yyyy
    //     Updated the nordpool daily data for tomorrow
    var notif_container = document.getElementById("notification-container");
    
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "/victron/get_nordpool_data",
        contentType: "application/json; charset=utf-8",
        data:  JSON.stringify({"range": false}),
        success: function (data) {
            console.log(data);
              data.forEach((element, id) => {
                  var notification_body = document.createElement('a');
                  notification_body.innerHTML = '<a class="dropdown-item d-flex align-items-center" href="#"><div class="me-3"><div class="bg-primary icon-circle notification_icon"><i class="fas fa-file-alt text-white"></i></div></div><div><span class="small text-gray-500 notification_time"></span><p class="notification_content">NordPool synced at '+ element.last_update_time +' </p></div></a>';
                  notif_container.appendChild(notification_body);
              });
        },
        error: function (error) {
            alert("There was a problem fetching and displaying the notifications.");
            console.log(error);
        }
    });
    
    const save_profile_settings = document.getElementById("save_profile_settings");
    if (save_profile_settings != null) {
        const form = document.getElementById("profile_data_form");
        function handleForm(event) { event.preventDefault(); } 
        form.addEventListener('submit', handleForm);
        const profile_username = document.getElementById("profile_username");
        const profile_email = document.getElementById("profile_email");
        
        get_current_user().then(function(){
            profile_email.value = user.email;
            profile_username.value = user.username;
                    
            save_profile_settings.addEventListener('click', function(){
                const submitter = document.querySelector("button[value=SaveProfile]");
                const formData = new FormData(form, submitter);
                $.ajax({
                    type: "POST",
                    url: "/auth/change_username",
                    contentType: "application/json; charset=utf-8",
                    dataType: 'json',
                    data:  JSON.stringify({"username": profile_username}),
                    success: function (data) {
                        alert("Please login with new credentials.")
                    },
                    error: function (error) {
                        console.log(error.responseText);
                        alert("error" + error.responseText);
                    }
                });
                $.ajax({
                    type: "POST",
                    url: "/auth/change_email",
                    contentType: "application/json; charset=utf-8",
                    dataType: 'json',
                    data:  JSON.stringify({"email": profile_email}),
                    success: function (data) {
                        console.log(data);
                    },
                    error: function (error) {
                        console.log(error.responseText);
                        alert("error" + error.responseText);
                    }
                });
            });
        });
    }

    const save_victron_settings = document.getElementById("save_victron_settings");
    if (save_victron_settings != null) {
        const show_password = document.getElementById("show_password");
        show_password.addEventListener('click', function(){
            var password = document.getElementById("victron_password");
            if (password.type === "password") {
                password.type = "text";
            } else {
                password.type = "password";
            }
        });
        save_victron_settings.addEventListener('click', function(){
            const form = document.getElementById("victron_energy_data_form");
            function handleForm(event) { event.preventDefault(); } 
            form.addEventListener('submit', handleForm);
            const submitter = document.querySelector("button[value=SaveVE]");
            const formData = new FormData(form, submitter);

            const portal_id = document.getElementById("portal_id").value;
            const price_to_compare = document.getElementById("price_to_compare").value;
            const email = document.getElementById("victron_email").value;
            const password = document.getElementById("victron_password").value;

            get_current_user().then(function(){
                $.ajax({
                    type: "POST",
                    url: "/victron/set_victron_data",
                    contentType: "application/json; charset=utf-8",
                    dataType: 'json',
                    data:  JSON.stringify({"portal_id": portal_id, "price_to_compare": price_to_compare, "email": email, "password": password, "user_email": user["email"]}),
                    success: function (data) {
                        const victron_notification = document.getElementById("victron_notification");
                        victron_notification.classList.add("success")
                        victron_notification.textContent = "Profile data updated!";
                    },
                    error: function (error) {
                        console.log(error.responseText);
                        alert("error" + error.responseText);
                    }
                });
            });
        });
    }

    const victron_energy_data_form = document.getElementById("victron_energy_data_form");
    if (victron_energy_data_form != null) {

        const instructions_button = document.getElementById("instructions_button");
        var x = document.getElementById("instructions");
        x.style.display = "none";
        instructions_button.addEventListener('click', function(){
            if (x.style.display === "none" ) {
                x.style.display = "block";
            } else {
                x.style.display = "none";
            }
        });
        const sleep = ms => new Promise(r => setTimeout(r, ms));
        const portal_id = document.getElementById("portal_id");
        const price_to_compare = document.getElementById("price_to_compare");
        const email = document.getElementById("victron_email");
        const password = document.getElementById("victron_password");

        get_current_user().then(function(){
            data_to_send = {"user_email": user["email"]}
            $.ajax({
                type: "POST",
                url: "/victron/get_victron_data",
                contentType: "application/json; charset=utf-8",
                dataType: 'json',
                data:  JSON.stringify(data_to_send),
                success: function (data) {
                    if (data["portal_id"]) {
                        portal_id.value = data["portal_id"];
                        price_to_compare.value = data["price_to_compare"];
                        email.value = data["email"];
                        password.value = data["password"];
                    }
                },
                error: function (error) {
                    const victron_notification = document.getElementById("victron_notification");
                    victron_notification.classList.add("error")
                    victron_notification.textContent = JSON.parse(error.responseText)["detail"];
                }
            });
        });
    }

    function logout_user() {
        $.ajax({
            type: "POST",
            dataType: "json",
            url: "/auth/logout",
            success: function (data) {
                window.location = '/login';
            }
        });
    }

    const a = document.getElementById("logout_button")
    if (a != null) {
        a.addEventListener("click", function(event) {
            event.preventDefault();
            logout_user();
        });
    }

    const ctx = document.getElementById('day-price-chart');
    var period = "1";
    if (ctx != null) {
        const last_update_time = document.getElementById("last_update_time");
        $.ajax({
            type: "POST",
            dataType: "json",
            url: "/victron/get_nordpool_data",
            contentType: "application/json; charset=utf-8",
            data:  JSON.stringify({"range": false}),
            success: function (data) {
                last_update_time.textContent = "Updated: " + data[0].last_update_time.toString().replace("T", " ");
            }
        });
        let chart;
        function getNordpoolPrices() {
            $.ajax({
                type: "POST",
                dataType: "json",
                url: "/victron/get_nordpool_prices",
                contentType: "application/json; charset=utf-8",
                data:  JSON.stringify({'period': period}),
                success: function (data) {
                    var labels = [];
                    var labels_time = [];
                    var values = [];
                    data.forEach((element, id) => {
                        labels.push(element.start_time.toString().substring(0,10));
                        labels_time.push(element.start_time.toString().substr(element.start_time.toString().length - 8, 5));
                        values.push(element.price);
                    });
                    
                    if (chart) {
                        chart.destroy();
                    }
                    // if (labels.length > 24){
                    //     limit=15
                    // } else {
                    //     limit=20
                    // }
                    limit=1000;
                    chart = new Chart(ctx, {
                        type: 'line',
                        data: {
                        labels: labels,
                        datasets: [{
                            label: 'Price in EUR',
                            data: values,
                            borderWidth: 1,
                        }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                x: {
                                    ticks: {
                                        maxTicksLimit: limit,
                                        }
                                    }
                                }
                            }
                        }
                    );
                },
                error: function (error) {
                    alert("error" + error.responseText);
                },
                always: function () {
                    alert("Always");
                }
            });
        }
        getNordpoolPrices();
        // Get the container element
        var btnContainer = document.getElementById("period_changer");
        // Get all buttons with class="btn" inside the container
        var btns = btnContainer.getElementsByClassName("period_button");
        var periodEl = document.getElementById("period");
        var current = btnContainer.getElementsByClassName("active");
        for (var i = 0; i < btns.length; i++) {
            btns[i].addEventListener("click", function() {
              current[0].className = current[0].className.replace(" active", "");
              this.className += " active";
              current = btnContainer.getElementsByClassName("active");
              periodEl.textContent = this.textContent;
                if (this.id == "today_prices") {
                    period = "1";
                } else if (this.id == "three_days_prices") {
                    period = "3";
                } else if (this.id == "week_prices") {
                    period = "7";
                } else if (this.id == "month_prices") {
                    period = "30";
                }
              getNordpoolPrices();
            });
        }
        if (!document.getElementById("period").textContent) {
            periodEl.textContent = current[0].textContent;
        }
    }

    const param_ctx = document.getElementById('param-price-chart');
    if (param_ctx != null) {
        let paramChart;
        let param="all";
        function getNordpoolPricesWithParam() {
            $.ajax({
                type: "POST",
                dataType: "json",
                url: "/victron/get_nordpool_data",
                contentType: "application/json; charset=utf-8",
                data:  JSON.stringify({"range": true}),
                success: function (data) {
                    var labels = [];
                    var labels_time = [];
                    var values = [];
                    min_v = [];
                    max_v = [];
                    avg_v = [];
                    data.forEach((element, id) => {
                        labels.push(element.last_update_time.toString().substring(0,10));
                        labels_time.push(element.last_update_time.toString().substr(element.last_update_time.toString().length - 8, 5));
                        min_v.push(element.min_price);
                        avg_v.push(element.avg_price);
                        max_v.push(element.max_price);
                    });
                    min_dataset = {
                        label: 'Minimum',
                        data: min_v,
                        borderWidth: 1,
                    };
                    max_dataset = {
                        label: 'Maximum',
                        data: max_v,
                        borderWidth: 1,
                    };
                    avg_dataset = {
                        label: 'Average',
                        data: avg_v,
                        borderWidth: 1,
                    };

                    res_dataset = [];

                    if (param == "min") {
                        res_dataset.push(min_dataset);
                    }
                    else if (param == "max") {
                        res_dataset.push(max_dataset);
                    }
                    else if (param == "avg") {
                        res_dataset.push(avg_dataset);
                    }
                    else if (param == "all") {
                        res_dataset.push(min_dataset);
                        res_dataset.push(max_dataset);
                        res_dataset.push(avg_dataset);
                    }
                    
                    console.log(labels);
                    if (paramChart) {
                        console.log("WE IN");
                        paramChart.destroy();
                    }
                    limit=1000;
                    paramChart = new Chart(param_ctx, {
                        type: 'line',
                        data: {
                        labels: labels,
                        datasets: res_dataset,
                        },
                        options: {
                            responsive: true,
                            interaction: {
                                mode: 'index',
                                intersect: false,
                            },
                            scales: {
                                x: {
                                    ticks: {
                                        maxTicksLimit: limit,
                                        }
                                    }
                                }
                            }
                        }
                    );
                },
                error: function (error) {
                    alert("error" + error.responseText);
                },
                always: function () {
                    alert("Always");
                }
            });
        }
        getNordpoolPricesWithParam();
        var paramBtnContainer = document.getElementById("parameter_changer");
        // Get all buttons with class="btn" inside the container
        var paramBtns = paramBtnContainer.getElementsByClassName("param_button");
        var paramEl = document.getElementById("param_display");
        var currentParam = paramBtnContainer.getElementsByClassName("active");
        for (var i = 0; i < paramBtns.length; i++) {
            paramBtns[i].addEventListener("click", function() {
              currentParam[0].className = currentParam[0].className.replace(" active", "");
              this.className += " active";
              currentParam = paramBtnContainer.getElementsByClassName("active");
              paramEl.textContent = this.textContent;
                if (this.id == "min_prices") {
                    param = "min";
                } else if (this.id == "max_prices") {
                    param = "max";
                } else if (this.id == "avg_prices") {
                    param = "avg";
                } else if (this.id == "all_prices") {
                    param = "all";
                }
                getNordpoolPricesWithParam();
            });
        }
        if (!document.getElementById("param_display").textContent) {
            paramEl.textContent = currentParam[0].textContent;
        }
    }
    
});