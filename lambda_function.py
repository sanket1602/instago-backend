var HMACAuth = require('BankCloudAuth');
var kinsurance = require('KotakCalcPremium');


exports.handler = async (event) => {

    const promise = new Promise(function (resolve, reject) {

        HMACAuth.LogDetails("Insurance_lambda", "EVENT:  " + JSON.stringify(event));

        var authHeader = HMACAuth.ValidateRequestAndGetUserId(event.headers.Authorization, JSON.stringify(event.body), event.url);
        authHeader.then(function (authHeaderResult) {
            console.log('authresult: ', authHeaderResult);

            var inputdata = event.body;
            var RouteId = Number(inputdata.route);

            console.log("URN ", inputdata.urn);

            var valInput = validateInput(inputdata);
            valInput.then(function (valInputRes) {
                console.log("valInputRes ", valInputRes);

                if (valInputRes == '') {

                    if (inputdata.consumerData != undefined && inputdata.consumerData.length != undefined) {

                        var loopConsumerRes = loopConsumer(inputdata);
                        loopConsumerRes.then(function (consumerDataRes) {
                            console.log("consumerDataRes ", consumerDataRes);

                            if (consumerDataRes == "") {

                                var bcrecordres = HMACAuth.GetBCTransactionsByURN(inputdata.urn);
                                bcrecordres.then(function (DDLogResult) {

                                    if (DDLogResult.length <= 0) {

                                        console.log("inputdata index ", inputdata);

                                        if (isNaN(RouteId) == false) {
                                            console.log("P : RRB Start");
                                            var rrbInfo = HMACAuth.InvokeRoundRobinWithRoute(RouteId);
                                            rrbInfo.then(function (rrbInfoResult) {
                                                console.log("P : RRB End");

                                                console.log("rrbInfoResult ", rrbInfoResult);

                                                if (authHeaderResult.TenantId == rrbInfoResult.TenantId) {

                                                    if (rrbInfoResult.ServiceAgentId == 26) {
                                                        var kotakInsRes = kinsurance.CalculatePremimum(rrbInfoResult, inputdata, authHeaderResult);
                                                        kotakInsRes.then(function (kInsResponse) {
                                                            console.log("kInsResponse ", kInsResponse);
                                                            resolve(kInsResponse);
                                                        });
                                                    }
                                                    else {
                                                        errorData = HMACAuth.GetGenericErrorDetailsByCode('BCGEN0003');
                                                        errorData.then(function (errorDataResult) {
                                                            console.log("route");
                                                            resolve(errorDataResult);
                                                        });
                                                    }

                                                } else {
                                                    var errorData = HMACAuth.GetGenericErrorDetailsByCode('BCGEN0101');
                                                    errorData.then(function (errorDataResult) {
                                                        var resolveObj = {
                                                            CalPremiumResponse: errorDataResult
                                                        };
                                                        resolve(resolveObj);
                                                    });
                                                }
                                            });
                                        }
                                        else {
                                            var errorData = HMACAuth.GetGenericErrorDetailsByCode('BCGEN0101');
                                            errorData.then(function (errorDataResult) {
                                                var resolveObj = {
                                                    CalPremiumResponse: errorDataResult
                                                };
                                                resolve(resolveObj);
                                            });
                                        }

                                    }
                                    else {
                                        var errorData = HMACAuth.GetGenericErrorDetailsByCode('BCGEN0006');
                                        errorData.then(function (errorDataResult) {
                                            console.log("errorDataResult: ", errorDataResult);
                                            var resolveObj = {
                                                CalPremiumResponse: errorDataResult
                                            };

                                            resolve(resolveObj);
                                        });
                                    }

                                });

                            }
                            else {
                                console.log("Invalid ConsumerData");
                                resolve(consumerDataRes);
                            }
                        });

                    }
                    else {
                        console.log("Invalid ConsumerData object");
                        resolve({ "Message": "Invalid ConsumerData object" });
                    }

                }
                else {
                    console.log("Input Validation Failed");
                    resolve(valInputRes);
                }
            });

        }).catch(function (err) {
            console.log("error at authentication");
            console.log(err);
            resolve(err);
        });

    });
    return promise;
};


function validateInput(inputdata) {

    const promise = new Promise(function (resolve, reject) {

        var errorData;

        console.log("Input validation ");

        if (inputdata.route == undefined || inputdata.route == null || inputdata.route == "" || inputdata.route == 0) {
            errorData = HMACAuth.GetGenericErrorDetailsByCode('BCGEN0003');
            errorData.then(function (errorDataResult) {
                console.log("route");
                resolve(errorDataResult);
            });
        }

        else if (inputdata.urn == undefined || inputdata.urn == null || inputdata.urn == "") {
            errorData = HMACAuth.GetGenericErrorDetailsByCode('BCGEN0006');
            errorData.then(function (errorDataResult) {
                console.log("urn");
                resolve(errorDataResult);
            });
        }

        else if (inputdata.loan_details == undefined || inputdata.loan_details == null || inputdata.loan_details == "") {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT003');
            errorData.then(function (errorDataResult) {
                console.log("loanDetails");
                resolve(errorDataResult);
            });
        }

        else if (inputdata.loan_details && inputdata.loan_details.policyterm == undefined || inputdata.loan_details.policyterm == null || inputdata.loan_details.policyterm == "") {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT004');
            errorData.then(function (errorDataResult) {
                console.log("policyTerm");
                resolve(errorDataResult);
            });
        }

        else if (inputdata.loan_details && inputdata.loan_details.sumassured == undefined || inputdata.loan_details.sumassured == null || inputdata.loan_details.sumassured == "") {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT005');
            errorData.then(function (errorDataResult) {
                console.log("sumAssured");
                resolve(errorDataResult);
            });
        }

        else if (inputdata.loan_details && inputdata.loan_details.loantype == undefined || inputdata.loan_details.loantype == null || inputdata.loan_details.loantype == "") {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT006');
            errorData.then(function (errorDataResult) {
                console.log("loanType");
                resolve(errorDataResult);
            });
        }

        else if (inputdata.loan_details && inputdata.loan_details.loanstartdate == undefined || inputdata.loan_details.loanstartdate == null || inputdata.loan_details.loanstartdate == "") {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT007');
            errorData.then(function (errorDataResult) {
                console.log("loanstartdate");
                resolve(errorDataResult);
            });
        }

        else if (inputdata.loan_details && (inputdata.loan_details.loanstartdate != undefined && inputdata.loan_details.loanstartdate != null && inputdata.loan_details.loanstartdate != "") && (dateFormatCheck(inputdata.loan_details.loanstartdate) == true)) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT007');
            errorData.then(function (errorDataResult) {
                console.log("loanstartdate1");
                resolve(errorDataResult);
            });
        }

        // else if (inputdata.loan_details && (inputdata.loan_details.loanenddate != undefined && inputdata.loan_details.loanenddate != null && inputdata.loan_details.loanenddate != "") && dateFormatCheck(inputdata.loan_details.loanenddate)) {
        //     errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT007');
        //     errorData.then(function (errorDataResult) {
        //         console.log("loanstartdate2");
        //         resolve(errorDataResult);
        //     });
        // }
        // else if (dateComparision(inputdata.loan_details.loanstartdate, inputdata.loan_details.loanenddate)) {
        //     errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT007');
        //     errorData.then(function (errorDataResult) {
        //         console.log("loanstartdate3");
        //         resolve(errorDataResult);
        //     });
        // }
        else if (inputdata.loan_details && inputdata.loan_details.loanamount != undefined && inputdata.loan_details.loanamount != null && inputdata.loan_details.loanamount != "" && (/^[0-9]*$/.test(inputdata.loan_details.loanamount.toString()) == false)) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT010');
            errorData.then(function (errorDataResult) {
                console.log("loanamount");
                resolve(errorDataResult);
            });
        }

        // else if (inputdata.loan_details && inputdata.loan_details.loanid == undefined || inputdata.loan_details.loanid == null || inputdata.loan_details.loanid == "") {
        //     errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT016');
        //     errorData.then(function (errorDataResult) {
        //         console.log("loanid");
        //         resolve(errorDataResult);
        //     });
        // }

        // else if (inputdata.loan_details && inputdata.loan_details.nompercent == undefined || inputdata.loan_details.nompercent == null || inputdata.loan_details.nompercent == "") {
        //     errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT021');
        //     errorData.then(function (errorDataResult) {
        //         console.log("nompercent");
        //         resolve(errorDataResult);
        //     });
        // }

        else if (inputdata.loan_details && inputdata.loan_details.plancode == undefined || inputdata.loan_details.plancode == null || inputdata.loan_details.plancode == "") {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT029');
            errorData.then(function (errorDataResult) {
                console.log("plancode");
                resolve(errorDataResult);
            });
        }

        else if (inputdata.loan_details && inputdata.loan_details.policymode == undefined || inputdata.loan_details.policymode == null || inputdata.loan_details.policymode == "") {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT030');
            errorData.then(function (errorDataResult) {
                console.log("policymode");
                resolve(errorDataResult);
            });
        }

        else {
            console.log("Validation success at Input Data");
            resolve("");
        }

    });

    return promise;

}


function validateBorrowerObject(BorrowerObj) {

    const promise = new Promise(function (resolve, reject) {

        console.log("borrowerObj ", BorrowerObj);

        var errorData;

        /////// BORROWER VALIDATION ///////////////////////////////////////////////////////

        if (BorrowerObj.consumertype.toLowerCase() == "borrower" && (BorrowerObj.dob == undefined || BorrowerObj.dob == null || BorrowerObj.dob == "")) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT008');
            errorData.then(function (errorDataResult) {
                console.log("Date of birth");
                resolve(errorDataResult);
            });
        }

        else if (BorrowerObj.consumertype.toLowerCase() == "borrower" && (BorrowerObj.dob != undefined && BorrowerObj.dob != null && BorrowerObj.dob != "") && (dateFormatCheck(BorrowerObj.dob) == true)) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT008');
            errorData.then(function (errorDataResult) {
                console.log("loanstartdate1");
                resolve(errorDataResult);
            });
        }

        else if (BorrowerObj.consumertype.toLowerCase() == "borrower" && (BorrowerObj.dob != undefined && BorrowerObj.dob != null && BorrowerObj.dob != "") && dateFormatCheck(BorrowerObj.dob)) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT008');
            errorData.then(function (errorDataResult) {
                console.log("loanstartdate2");
                resolve(errorDataResult);
            });
        }

        else if (BorrowerObj.consumertype.toLowerCase() == "borrower" && (BorrowerObj.gender == undefined || BorrowerObj.gender == null || BorrowerObj.gender == "")) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT009');
            errorData.then(function (errorDataResult) {
                console.log("gender");
                resolve(errorDataResult);
            });
        }

        else if (BorrowerObj.consumertype.toLowerCase() == "borrower" && (BorrowerObj.custsalutation == undefined || BorrowerObj.custsalutation == null || BorrowerObj.custsalutation == "")) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT023');
            errorData.then(function (errorDataResult) {
                console.log("gender");
                resolve(errorDataResult);
            });
        }


        else if (BorrowerObj.consumertype.toLowerCase() == "borrower" && (BorrowerObj.custname == undefined || BorrowerObj.custname == null || BorrowerObj.custname == "")) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT025');
            errorData.then(function (errorDataResult) {
                console.log("gender");
                resolve(errorDataResult);
            });
        }

        else if (BorrowerObj.consumertype.toLowerCase() == "borrower" && (BorrowerObj.cif_id == undefined || BorrowerObj.cif_id == null || BorrowerObj.cif_id == "")) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT022');
            errorData.then(function (errorDataResult) {
                console.log("gender");
                resolve(errorDataResult);
            });
        }

        else if (BorrowerObj.consumertype.toLowerCase() == "borrower" && (BorrowerObj.addressline1 == undefined || BorrowerObj.addressline1 == null || BorrowerObj.addressline1 == "")) {
            errorData = HMACAuth.GetErrorDetailsByCode(19, 'INCPKT026');
            errorData.then(function (errorDataResult) {
                console.log("gender");
                resolve(errorDataResult);
            });
        }

        else {
            console.log("Consumer validation success");
            resolve("");
        }

    });

    return promise;

}

function loopConsumer(inputdata) {

    const promise = new Promise(function (resolve, reject) {

        var flag = 0;

        for (let i = 0; i < inputdata.consumerData.length; i++) {

            var BorrowerObject = inputdata.consumerData[i];

            if (inputdata.consumerData[i].consumertype.toLowerCase() == "borrower") {

                flag = 1;
                var BorrowerValRes = validateBorrowerObject(BorrowerObject);
                BorrowerValRes.then(function (borrowerResult) {
                    console.log("borrowerResult loopConsumer ", borrowerResult);
                    resolve(borrowerResult);
                });


            }
            else if ((flag == 0) && (i == inputdata.consumerData.length - 1)) {
                resolve({ "Message": "Borrower Data is missing" });
            }

        }


    });

    return promise;

}

function dateComparision(stDate, endDate) {

    console.log("Date comparision1 ", stDate, endDate);

    var MstartDate = new Date(Number(stDate.split("/")[1]) + "/" + Number(stDate.split("/")[0]) + "/" + Number(stDate.split("/")[2]));
    var MendDate = new Date(Number(endDate.split("/")[1]) + "/" + Number(endDate.split("/")[0]) + "/" + Number(endDate.split("/")[2]));

    var result = (MstartDate > MendDate);
    return result;

}

function dateFormatCheck(date) {

    console.log("Date format check ", date);
    if (date.toString().search('/') == -1) {
        return true;
    }

    var res = date.toString().split('/');
    console.log(res[0].toString().length, res[1].toString().length, res[2].toString().length);
    if (res[0] && res[1] && res[2] && (res[0].toString().length != 2 || res[1].toString().length != 2 || res[2].toString().length != 4)) {
        return true;
    }
}

################
