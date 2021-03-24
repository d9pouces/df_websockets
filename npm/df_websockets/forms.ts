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
declare global {
    interface Window {
        DFSignals: any;
    }
}

export function serializeForm(form: HTMLFormElement) {
    /*
    Serialize a HTMLFormElement as a list of {name: <field name>, value: <field value>}
    disabled/reset/submit/buttonf fields are ignored
     */
    const serialized = [];
    // Loop through each field in the form
    for (let i = 0; i < form.elements.length; i++) {
        const field = <HTMLInputElement | HTMLSelectElement>form.elements[i];
        // Respect the same rules as jQuery's serializeArray
        if (!(<HTMLInputElement>field).name || (<HTMLInputElement>field).disabled || field.type === 'reset' || field.type === 'submit' || field.type === 'button') {
            continue;
        }
        if (field.type === "file") {  // just returns the name of selected files
            for (let n = 0; n < (<HTMLInputElement>field).files.length; n++) {
                serialized.push({name: field.name, value: (<HTMLInputElement>field).files[n].name});
            }
        } else if (field.type === 'select-multiple') { // get all selected options
            for (let n = 0; n < (<HTMLSelectElement>field).selectedOptions.length; n++) {
                serialized.push({name: field.name, value: (<HTMLSelectElement>field).selectedOptions[n].value});
            }
        } else if ((field.type !== 'checkbox' && field.type !== 'radio') || (<HTMLInputElement>field).checked) {
            serialized.push({name: field.name, value: field.value});
        }
    }
    return serialized;
}

function setFormFieldValue(form: HTMLFormElement, name: string, value: string | boolean | Array<string>) {
    const item = form.elements.namedItem(name);
    if (item === null) {
        return;
    } else if (item instanceof RadioNodeList) {
        if ((value === true) || (value === false)) {
            item.forEach((input: HTMLInputElement) => {
                input.checked = value
            });
        } else if (Array.isArray(value)) {
            const valuesSet = new Set(value);
            item.forEach((input: HTMLInputElement) => {
                input.checked = valuesSet.has(input.value);
            });
        } else {
            item.forEach((input: HTMLInputElement) => {
                input.checked = input.value === value;
            });
        }
    } else if (item instanceof HTMLTextAreaElement) {
        item.value = <string>value;
    } else if ((item instanceof HTMLInputElement) && (item.type === "checkbox")) {
        if (value === true) {
            item.checked = true;
        } else if (value === false) {
            item.checked = false;
        } else {
            item.value = <string>value;
        }
    } else if (item instanceof HTMLSelectElement) {
        const options = item.options;
        if (Array.isArray(value)) {
            const valuesSet = new Set(value);
            for (let i = 0; i < options.length; i++) {
                options[i].selected = valuesSet.has(options[i].value);
            }
        } else {
            for (let i = 0; i < options.length; i++) {
                options[i].selected = options[i].value === value;
            }
        }
    } else if (item instanceof HTMLInputElement) {
        item.value = <string>value;
    }

}


interface formSingleValue {
    name: string;
    value: string | Array<string> | boolean;
}

interface formValueList {
    selector: string;
    values: Array<formSingleValue>;
}

export function htmlFormsSet(opts: formValueList) {
    document.querySelectorAll(opts.selector).forEach(
        (form: HTMLFormElement) => {
            opts.values.forEach(
                (values) => {
                    setFormFieldValue(form, values.name, values.value);
                }
            )

        }
    );
}


interface Signal {
    name: string,
    on: string,
    form: string,
    opts: Record<string, any>,
    value: string,
    prevent: boolean
}

function DOMContentAdded(evt: Event) {
    /*
    search all HTML elements with an attribute "data-df-signal" that contains a JSON list of Signal objects:
    {
        name: "name of the signal to call",  (required)
        on: "name of the listened event",
        opts: "extra options",               (optional)
        form: "name of option to add to opts that contains the serialized form",  (optional)
        value: "name of option to add to opts that contains the value",  (optional)
        prevent: preventDefault               (optional, defaults to true for on=="submit" or "click" else false )
    }

    When the listened event is not given, the listened event is
        * "submit" for forms,
        * "click" for "reset"/"submit"/"button" input fields,
        * "change" for other fields.

    Using on a HTML form:
    ```html
    <form data-df-signal='[{"name": "signal.name", "on": "change", "form": "form_data", "opts": {"id": 42} }]'>
        <input type="text" name="title" value="df_websockets">
    </form>```
    or, using the Django templating system:
    ```html
    {% load df_websockets %}
    <form {% js_call "signal.name" on="change" form="form_data" id=42 %}>
        <input type="text" name="title" value="df_websockets">
    </form>```

    When the field "title" is modified, a signal "signal.name" is triggered on the server (via the websocket) with
    the following arguments:
    ```python
    form_data = [{"name": "title", "value": "df_websockets"}]
    id = 42
    ```

    Using on a HTML form input field:
    ```html
    <form>
        <input type="text" name="title" data-df-signal='[{"name": "signal.name", "on": "change", "value": "title", "opts": {"id": 42} }]'>
    </form>```
    or, using the Django templating system:
    ```html
    {% load df_websockets %}
    <form>
        <input type="text" name="title" {% js_call "signal.name" on="change" value="title" id=42 %}>
    </form>```

    When the field "title" is modified, a signal "signal.name" is triggered on the server (via the websocket) with
    the following arguments:
    ```python
    title = "new title value"
    id = 42
    ```
     */
    (<HTMLElement>evt.target).querySelectorAll("[data-df-signal]").forEach(
        (target: HTMLInputElement | HTMLSelectElement | HTMLFormElement) => {
            const signals = <Array<Signal>>JSON.parse(target.getAttribute("data-df-signal"));
            signals.forEach((signal: Signal) => {
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
                const callback = (evt: Event) => {
                    // noinspection JSUnresolvedVariable
                    const prevent = signal.prevent;
                    const opts = signal.opts || {};
                    if (signal.form) {
                        opts[signal.form] = serializeForm(<HTMLFormElement>target);
                    }
                    if (signal.value) {

                        if (target.type === "file") {  // just returns the name of selected files
                            opts[signal.value] = [];
                            for (let n = 0; n < (<HTMLInputElement>target).files.length; n++) {
                                opts[signal.value].push((<HTMLInputElement>target).files[n].name);
                            }
                        } else if (target.type === 'select-multiple') { // get all selected options
                            opts[signal.value] = [];
                            for (let n = 0; n < (<HTMLSelectElement>target).selectedOptions.length; n++) {
                                opts[signal.value].push((<HTMLSelectElement>target).selectedOptions[n].value);
                            }
                        } else if (target.type === 'checkbox' || target.type === 'radio') {
                            opts[signal.value] = (<HTMLInputElement>target).checked;

                        } else {
                            opts[signal.value] = target.value;
                        }
                    }
                    (<Window>window).DFSignals.call(
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
document.addEventListener("DOMContentLoaded", (evt) => {
    window.setTimeout(() => {
        DOMContentAdded(evt);
    }, 200);
    // awful trick for being sure that our addEventListener is the last.
    // allows things like CKEditor to push its content to the textarea before sending the content of the form.
});