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

export const htmlAfter = opts => {
    document.querySelectorAll(opts.selector).forEach(elt => {
        const originalNextSibling = elt.nextSibling;
        elt.insertAdjacentHTML('afterend', opts.content);
        let sibling = elt.nextSibling;
        while (sibling && (sibling !== originalNextSibling)) {
            if (sibling.querySelectorAll) {
                sibling.dispatchEvent(new Event('DOMContentAdded', {bubbles: true}));
            }
            sibling = sibling.nextSibling;
        }
    });
};
export const htmlAppend = opts => {
    document.querySelectorAll(opts.selector).forEach(elt => {
        const originalLastChild = elt.lastChild;
        elt.insertAdjacentHTML('beforeend', opts.content);
        let child = elt.lastChild;
        while (child && (child !== originalLastChild)) {
            if (child.querySelectorAll) {
                child.dispatchEvent(new Event('DOMContentAdded', {bubbles: true}));
            }
            child = child.previousSibling;
        }
    });
};
export const htmlPrepend = opts => {
    document.querySelectorAll(opts.selector).forEach(elt => {
        const originalFirstChild = elt.firstChild;
        elt.insertAdjacentHTML('afterbegin', opts.content);
        let child = elt.firstChild;
        while (child && (child !== originalFirstChild)) {
            if (child.querySelectorAll) {
                child.dispatchEvent(new Event('DOMContentAdded', {bubbles: true}));
            }
            child = child.nextSibling;
        }
    });
};
export const htmlBefore = opts => {
    document.querySelectorAll(opts.selector).forEach(elt => {
        const originalPreviousSibling = elt.previousSibling;
        elt.insertAdjacentHTML('beforebegin', opts.content);
        let sibling = elt.previousSibling;
        while (sibling && (sibling !== originalPreviousSibling)) {
            if (sibling.querySelectorAll) {
                sibling.dispatchEvent(new Event('DOMContentAdded', {bubbles: true}));
            }
            sibling = sibling.previousSibling;
        }
    });
};
export const htmlContent = (opts) => {
    document.querySelectorAll(opts.selector).forEach(elt => {
        elt.innerHTML = opts.content;
        let child = elt.firstChild;
        while (child) {
            if (child.querySelectorAll) {
                child.dispatchEvent(new Event('DOMContentAdded', {bubbles: true}));
            }
            child = child.nextSibling;
        }
    });
};
export const htmlReplaceWith = (opts) => {
    document.querySelectorAll(opts.selector).forEach(elt => {
            const previousSibling = elt.previousSibling;
            const nextSibling = elt.nextSibling;
            const parentNode = elt.parentNode;
            elt.outerHTML = opts.content;
            let sibling = parentNode.firstChild;
            if (previousSibling) {
                sibling = previousSibling.nextSibling;
            }
            while (sibling && (sibling !== nextSibling)) {
                if (sibling.querySelectorAll) {
                    sibling.dispatchEvent(new Event('DOMContentAdded', {bubbles: true}));
                }
                sibling = sibling.nextSibling;
            }
        }
    )
    ;
};
export const htmlEmpty = opts => {
    document.querySelectorAll(opts.selector).forEach(elt => {
        while (elt.firstChild) {
            elt.removeChild(elt.firstChild);
        }
    });
};
export const htmlRemove = opts => {
    document.querySelectorAll(opts.selector).forEach(elt => {
        elt.parentNode.removeChild(elt);
    });
};
export const htmlText = (opts) => {
    document.querySelectorAll(opts.selector).forEach(elt => {
        elt.textContent = opts.content;
    });
};
