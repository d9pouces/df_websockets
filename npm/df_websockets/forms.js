////////////////////////////////////////////////////////////////////////////////
// This file is part of df_websockets                                          /
//                                                                             /
// Copyright (C) 2020 Matthieu Gallet <github@19pouces.net>                    /
// All Rights Reserved                                                         /
//                                                                             /
// You may use, distribute and modify this code under the                      /
// terms of the (BSD-like) CeCILL-B license.                                   /
//                                                                             /
// You should have received a copy of the CeCILL-B license with                /
// this file. If not, please visit:                                            /
// https://cecill.info/licences/Licence_CeCILL-B_V1-en.txt (English)           /
// or https://cecill.info/licences/Licence_CeCILL-B_V1-fr.txt (French)         /
//                                                                             /
////////////////////////////////////////////////////////////////////////////////

export function serializeForm(form) {
    const serialized = [];
    // Loop through each field in the form
    for (let i = 0; i < form.elements.length; i++) {
        const field = form.elements[i];
        // Respect the same rules as jQuery's serializeArray
        if (!field.name || field.disabled || field.type === 'reset' || field.type === 'submit' || field.type === 'button') {
            continue;
        }
        if (field.type === "file") {  // just returns the name of selected files
            for (let n = 0; n < field.files.length; n++) {
                serialized.push({name: field.name, value: field.files[n].name});
            }
        } else if (field.type === 'select-multiple') { // get all selected options
            for (let n = 0; n < field.selectedOptions.length; n++) {
                serialized.push({name: field.name, value: field.selectedOptions[n].value});
            }
        } else if ((field.type !== 'checkbox' && field.type !== 'radio') || field.checked) {
            serialized.push({name: field.name, value: field.value});
        }
    }
    return serialized;
}


function DOMContentAdded(evt) {
    /*
    looks for an attribute "data-df-signal" that contains a JSON-list of objects:
    {
        name: "name of the signal to call",  (required)
        on: "name of the listened event",    (optional: defaults to "submit" for forms, "" )
        opts: "extra options",               (optional)
        form: "name of option to add to opts that contains the serialized form",  (optional)
        value: "name of option to add to opts that contains the value",  (optional)
        prevent: preventDefault               (optional, defaults to true for on=="change" else false )
    }
     */
    evt.target.querySelectorAll("[data-df-signal]").forEach(
        target => {
            const signals = JSON.parse(target.getAttribute("data-df-signal"));
            signals.forEach(signal => {
                let eventName = signal.on;
                if (!eventName) {
                    if (target.tagName === "FORM") {
                        eventName = "submit";
                    } else if ((target.tagName === "INPUT" && !(target.type === 'reset' || target.type === 'submit' || target.type === 'button')) || (target.tagName === "TEXTAREA")) {
                        eventName = "change";
                    } else {
                        eventName = "click";
                    }
                }
                const callback = evt => {
                    // noinspection JSUnresolvedVariable
                    const prevent = signal.prevent;
                    const opts = signal.opts || {};
                    if (signal.form) {
                        opts[signal.form] = serializeForm(target);
                    }
                    if (signal.value) {

                        if (target.type === "file") {  // just returns the name of selected files
                            opts[signal.value] = [];
                            for (let n = 0; n < target.files.length; n++) {
                                opts[signal.value].push(target.files[n].name);
                            }
                        } else if (target.type === 'select-multiple') { // get all selected options
                            opts[signal.value] = [];
                            for (let n = 0; n < target.selectedOptions.length; n++) {
                                opts[signal.value].push(target.selectedOptions[n].value);
                            }
                        } else if (target.type === 'checkbox' || target.type === 'radio') {
                            opts[signal.value] = target.checked;

                        } else {
                            opts[signal.value] = target.value;
                        }
                    }
                    window.DFSignals.call(
                        signal.name,
                        opts
                    );

                    if (prevent === true || (prevent === null && eventName !== "change")) {
                        evt.preventDefault();
                    }
                }
                target.addEventListener(eventName, callback);
            });
        }
    );
}


document.addEventListener("DOMContentAdded", (evt) => {
    window.setTimeout(() => {
        DOMContentAdded(evt);
    }, 200);
    // awful trick for being sure that our addEventListener is the last.
    // allows things like CKEditor to push its content to the textarea before sending the content of the form.
});