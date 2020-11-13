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

import {setFormInputValue} from "./forms";

function connectSignals() {

    // noinspection ES6ModulesDependencies
    window.DFSignals.connect('html.add_class', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            // noinspection JSUnresolvedVariable
            elt.classList.add(opts.class_name)
        });
    });
    /*"""
    .. function:: html.add_class(opts)

        Adds the specified class(es) to each of the set of matched elements.

        .. code-block:: javascript

            window.DFSignals.call('html.add_class', {selector: "#obj", class_name: "myclass"});


        .. code-block:: python

            trigger(window_info, 'html.add_class', to=WINDOW, selector="#obj", class_name="myclass")


        :param string selector: HTML selector
        :param string class_name: new class

    */

    window.DFSignals.connect('html.after', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.insertAdjacentElement('afterend', opts.content)
        });
    });
    /*"""
    .. function:: html.after(opts)

        Insert content, specified by the parameter, after each element in the set of matched elements..

        .. code-block:: javascript

            window.DFSignals.call('html.after', {selector: "#obj", content: "<span>hello</span>"});

        .. code-block:: python

            trigger(window_info, 'html.after', to=WINDOW, selector="#obj", content="<span>hello</span>")

        :param string selector: HTML selector
        :param string content: new HTML content

    */

    window.DFSignals.connect('html.append', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.append(opts.content)
        });
    });
    /*"""
    .. function:: html.append(opts)

        Insert content, specified by the parameter, to the end of each element in the set of matched elements.

        .. code-block:: javascript

            window.DFSignals.call('html.append', {selector: "#obj", content: "<span>hello</span>"});

        .. code-block:: python

            trigger(window_info, 'html.append', to=WINDOW, selector="#obj", content="<span>hello</span>")

        :param string selector: HTML selector
        :param string content: new HTML content

    */

    window.DFSignals.connect('html.before', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.insertAdjacentElement('beforebegin', opts.content)
        });
    });
    /*"""
    .. function:: html.before(opts)

        Insert content, specified by the parameter, before each element in the set of matched elements..

        .. code-block:: javascript

            window.DFSignals.call('html.before', {selector: "#obj", content: "<span>hello</span>"});

        .. code-block:: python

            trigger(window_info, 'html.before', to=WINDOW, selector="#obj", content="<span>hello</span>")

        :param string selector: HTML selector
        :param string content: new HTML content

    */

    window.DFSignals.connect('html.empty', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            while (elt.firstChild) {
                elt.removeChild(elt.firstChild);
            }
        });
    });
    /*"""
    .. function:: html.empty(opts)

        Remove all child nodes of the set of matched elements from the DOM.

        .. code-block:: javascript

            window.DFSignals.call('html.empty', {selector: "#obj"});

        .. code-block:: python

            trigger(window_info, 'html.empty', to=WINDOW, selector="#obj")

        :param string selector: HTML selector

    */

    window.DFSignals.connect('html.prepend', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.insertBefore(opts.content, parent.firstChild);
        });
    });
    /*"""
    .. function:: html.prepend(opts)

        Insert content, specified by the parameter, to the beginning of each element in the set of matched elements.

        .. code-block:: javascript

            window.DFSignals.call('html.prepend', {selector: "#obj", content: "<span>hello</span>"});

        .. code-block:: python

            trigger(window_info, 'html.prepend', to=WINDOW, selector="#obj", content="<span>hello</span>")

        :param string selector: HTML selector
        :param string content: new HTML content

    */

    window.DFSignals.connect('html.remove', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.parentNode.removeChild(elt)
        });
    });
    /*"""
    .. function:: html.remove(opts)

        Remove the set of matched elements from the DOM.

        .. code-block:: javascript

            window.DFSignals.call('html.remove', {selector: "#obj"});

        .. code-block:: python

            trigger(window_info, 'html.remove', to=WINDOW, selector="#obj")

        :param string selector: HTML selector

    */
    window.DFSignals.connect('html.remove_attr', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            // noinspection JSUnresolvedVariable
            elt.removeAttribute(opts.attr_name);
        });
    });
    /*"""
    .. function:: html.remove_attr(opts)

        Remove an attribute from each element in the set of matched elements.

        .. code-block:: javascript

            window.DFSignals.call('html.remove_attr', {selector: "#obj", attr_name: "attr"});

        .. code-block:: python

            trigger(window_info, 'html.remove_attr', to=WINDOW, selector="#obj", attr_name="attr")

        :param string selector: HTML selector
        :param string attr_name: attribute to remove

    */
    window.DFSignals.connect('html.remove_class', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            // noinspection JSUnresolvedVariable
            elt.classList.remove(opts.class_name);
        });
    });
    /*"""
    .. function:: html.remove_class(opts)

        Remove a single class, multiple classes, or all classes from each element in the set of matched elements.

        .. code-block:: javascript

            window.DFSignals.call('html.remove_class', {selector: "#obj", class_name: "class"});

        .. code-block:: python

            trigger(window_info, 'html.remove_class', to=WINDOW, selector="#obj", class_name="attr")

        :param string selector: HTML selector
        :param string class_name: class to remove

    */
    window.DFSignals.connect('html.replace_with', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.outerHTML = opts.content;
        });
    });
    /*"""
    .. function:: html.replace_with(opts)

        Replace each element in the set of matched elements with the provided new content.

        .. code-block:: javascript

            window.DFSignals.call('html.replace_with', {selector: "#obj", content: "<span>hello</span>"});

        .. code-block:: python

            trigger(window_info, 'html.replace_with', to=WINDOW, selector="#obj", content="<span>hello</span>")

        :param string selector: HTML selector
        :param string content: new HTML content

    */

    window.DFSignals.connect('html.add_attribute', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            // noinspection JSUnresolvedVariable
            elt.setAttribute(opts.attr_name, opts.attr_value);
        });
    });
    /*"""
    .. function:: html.add_attribute(opts)

        Add an attribute to each element matched by the given selector.

        .. code-block:: javascript

            window.DFSignals.call('html.add_attribute', {selector: "#obj", attr_name: "data-df", attr_value: "value"});

        .. code-block:: python

            trigger(window_info, 'html.add_attribute', to=WINDOW, selector="#obj", attr_name="data-df", attr_value= "value")


        :param string selector: HTML selector
        :param string attr_name: name of the attribute to add
        :param string attr_value: value of the attribute to add

    */

    window.DFSignals.connect('html.content', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.innerHTML = opts.content;
        });
    });
    /*"""
    .. function:: html.content(opts)

        set the HTML contents of every matched element.

        .. code-block:: javascript

            window.DFSignals.call('html.content', {selector: "#obj", content: "<span>hello</span>"});

        .. code-block:: python

            trigger(window_info, 'html.content', to=WINDOW, selector="#obj", content= "<span>hello</span>")


        :param string selector: HTML selector
        :param string content: new HTML content
    */


    window.DFSignals.connect('html.text', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.textContent = opts.content;
        });
    });
    /*"""
    .. function:: html.text(opts)

        Set the text contents of the matched elements.

        .. code-block:: javascript

            window.DFSignals.call('html.text', {selector: "#obj", content: "<span>hello</span>"});

        .. code-block:: python

            trigger(window_info, 'html.text', to=WINDOW, selector="#obj", content= "<span>hello</span>")


        :param string selector: HTML selector
        :param string content: new HTML content

    */

    window.DFSignals.connect('html.download_file', (opts) => {
        /*"""
        .. function:: html.download_file(opts)

            Force the client to download the given file.

            .. code-block:: javascript

                window.DFSignals.call('html.download_file', {url: "http://example.org/test.zip", filename: "test.zip"});

        .. code-block:: python

            trigger(window_info, 'html.download_file', to=WINDOW, url="http://example.org/test.zip", filename="test.zip")

            :param string url: URL of the file
            :param string filename: name of the file

        */
        const save = document.createElement('a');
        save.href = opts.url;
        save.target = '_blank';
        save.download = opts.filename || 'unknown';
        const evt = new MouseEvent('click', {view: window, bubbles: true, cancelable: false});
        save.dispatchEvent(evt);
        (window.URL || window.webkitURL).revokeObjectURL(save.href);
    });


    window.DFSignals.connect('html.focus', (opts) => {
        const elt = document.querySelector(opts.selector);
        if (elt) {
            elt.focus();
        }
    });
    /*"""
    .. function:: html.focus(opts)

        Set the focus to the matched element.

        .. code-block:: javascript

            window.DFSignals.call('html.focus', {selector: "#obj"});

        .. code-block:: python

            trigger(window_info, 'html.focus', to=WINDOW, selector="#obj")

        :param string selector: HTML selector

    */
    
    window.DFSignals.connect('html.forms.set', (opts) => {
        setFormInputValue(opts.selector, opts.value);
    });
    /*"""
    .. function:: html.forms.set(opts)

        Set the value of a form input

        .. code-block:: javascript

            window.DFSignals.call('html.forms.set', {selector: "[name=title]", value: "new title"});

        .. code-block:: python

            trigger(window_info, 'html.forms.set', to=WINDOW, selector="[name=title]", value="new_title")

        :param string selector: HTML selector

    */}

document.addEventListener("DOMContentLoaded", connectSignals);
