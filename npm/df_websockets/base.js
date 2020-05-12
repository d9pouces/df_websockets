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

function connectSignals() {

    // noinspection ES6ModulesDependencies
    DFSignals.connect('html.add_class', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            // noinspection JSUnresolvedVariable
            elt.classList.add(opts.class_name)
        });
    });
    /*"""
    .. function:: html.add_class(opts)

        Adds the specified class(es) to each of the set of matched elements.

        .. code-block:: javascript

            DFSignals.call('html.add_class', {selector: "#obj", class_name: "myclass"});

        :param string selector: jQuery selector
        :param string class_name: new class

    */

    DFSignals.connect('html.after', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.insertAdjacentElement('afterend', opts.content)
        });
    });
    /*"""
    .. function:: html.after(opts)

        Insert content, specified by the parameter, after each element in the set of matched elements..

        .. code-block:: javascript

            DFSignals.call('html.after', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */

    DFSignals.connect('html.append', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.append(opts.content)
        });
    });
    /*"""
    .. function:: html.append(opts)

        Insert content, specified by the parameter, to the end of each element in the set of matched elements.

        .. code-block:: javascript

            DFSignals.call('html.append', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */

    DFSignals.connect('html.before', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.insertAdjacentElement('beforebegin', opts.content)
        });
    });
    /*"""
    .. function:: html.before(opts)

        Insert content, specified by the parameter, before each element in the set of matched elements..

        .. code-block:: javascript

            DFSignals.call('html.before', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */

    DFSignals.connect('html.empty', opts => {
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

            DFSignals.call('html.empty', {selector: "#obj"});

        :param string selector: jQuery selector

    */

    DFSignals.connect('html.prepend', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.insertBefore(opts.content, parent.firstChild);
        });
    });
    /*"""
    .. function:: html.prepend(opts)

        Insert content, specified by the parameter, to the beginning of each element in the set of matched elements.

        .. code-block:: javascript

            DFSignals.call('html.prepend', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */

    DFSignals.connect('html.remove', opts => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.parentNode.removeChild(elt)
        });
    });
    /*"""
    .. function:: html.remove(opts)

        Remove the set of matched elements from the DOM.

        .. code-block:: javascript

            DFSignals.call('html.remove', {selector: "#obj"});

        :param string selector: jQuery selector

    */
    DFSignals.connect('html.remove_attr', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            // noinspection JSUnresolvedVariable
            elt.removeAttribute(opts.attr_name);
        });
    });
    /*"""
    .. function:: html.remove_attr(opts)

        Remove an attribute from each element in the set of matched elements.

        .. code-block:: javascript

            DFSignals.call('html.remove_attr', {selector: "#obj", attr_name: "attr"});

        :param string selector: jQuery selector
        :param string attr_name: attribute to remove

    */
    DFSignals.connect('html.remove_class', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            // noinspection JSUnresolvedVariable
            elt.classList.remove(opts.class_name);
        });
    });
    /*"""
    .. function:: html.remove_class(opts)

        Remove a single class, multiple classes, or all classes from each element in the set of matched elements.

        .. code-block:: javascript

            DFSignals.call('html.remove_class', {selector: "#obj", class_name: "class"});

        :param string selector: jQuery selector
        :param string class_name: class to remove

    */
    DFSignals.connect('html.replace_with', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.outerHTML = opts.content;
        });
    });
    /*"""
    .. function:: html.replace_with(opts)

        Replace each element in the set of matched elements with the provided new content.

        .. code-block:: javascript

            DFSignals.call('html.replace_with', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */

    DFSignals.connect('html.add_attribute', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            // noinspection JSUnresolvedVariable
            elt.setAttribute(opts.attr_name, opts.attr_value);
        });
    });
    /*"""
    .. function:: html.after(opts)

        Insert content, specified by the parameter, after each element in the set of matched elements..

        .. code-block:: javascript

            DFSignals.call('html.after', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */

    DFSignals.connect('html.content', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.innerHTML = opts.content;
        });
    });
    /*"""
    .. function:: html.content(opts)

        set the HTML contents of every matched element.

        .. code-block:: javascript

            DFSignals.call('html.content', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content
    */


    DFSignals.connect('html.text', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.textContent = opts.content;
        });
    });
    /*"""
    .. function:: html.text(opts)

        Set the text contents of the matched elements.

        .. code-block:: javascript

            DFSignals.call('html.text', {selector: "#obj", content: "<span>hello</span>"});


        :param string selector: jQuery selector
        :param string content: new HTML content

    */

    DFSignals.connect('html.download_file', (opts) => {
        /*"""
        .. function:: html.download_file(opts)

            Force the client to download the given file.

            .. code-block:: javascript

                DFSignals.call('html.download_file', {url: "http://example.org/test.zip", filename: "test.zip"});


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


    DFSignals.connect('html.focus', (opts) => {
        document.querySelectorAll(opts.selector).forEach(elt => {
            elt.focus();
        });
    });
    /*"""
    .. function:: html.focus(opts)

        Set the focus to the matched element.

        .. code-block:: javascript

            DFSignals.call('html.focus', {selector: "#obj"});

        :param string selector: jQuery selector

    */
}

document.addEventListener("DOMContentLoaded", connectSignals);
