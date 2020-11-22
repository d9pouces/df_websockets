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

window.DFSignals = {
    connection: null,
    buffer: [],
    registry: {},
    wsurl: null
};

function getCookie(cname) {
    const name = cname + "=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function websocketConnect() {
    const cookieName = "dfwsurl";
    if (window.DFSignals.wsurl === null) {
        const dfWsURL = getCookie(cookieName);
        window.DFSignals.wsurl = decodeURIComponent(dfWsURL);
    }
    if (!window.DFSignals.wsurl) {
        console.info("Unable to get the websocket URL in the '" + cookieName + "' cookie.");
        return;
    }
    const connection = new WebSocket(window.DFSignals.wsurl);
    /* cannot use header or cookies (cookies may change after the initial connection)
    *  so we use GET parameter
    *  */
    connection.onopen = () => {
        window.DFSignals.connection = connection;
        for (let i = 0; i < window.DFSignals.buffer.length; i++) {
            connection.send(window.DFSignals.buffer[i]);
        }
        window.DFSignals.buffer = [];
    };
    connection.onmessage = (e) => {
        console.debug('received call ' + e.data + ' from server.')
        const msg = JSON.parse(e.data);
        // noinspection JSUnresolvedVariable
        if (msg.signal && msg.signal_id) {
            window.DFSignals.call(msg.signal, msg.opts, msg.signal_id);
        }
    };
    connection.onerror = (e) => {
        console.error("WS error: " + e);
    };
    connection.onclose = () => {
        window.DFSignals.connection = null;
        setTimeout(websocketConnect, 3000);
    }
}

function call(signal, opts, id) {
    /*"""
    .. function:: call(signal, opts, id)

        Call a signal.
        If the signal is also defined in the Python server and available to the user, then the Python signal is also triggered.

        :param string signal: Name of the called signal.
        :param object opts: Object with signal arguments.
        :param string id: Unique id of each signal triggered by the server. Do not use it yourself.
        :returns: always `false`.
    */
    // if (window.DFSignals.registry[signal] === undefined) {
    //     console.debug('unknown call "' + signal + '" (from both client and server).');
    //     return false;
    // } else
    if ((id !== undefined) && (window.DFSignals.registry[id] !== undefined)) {
        return false;
    } else if (id !== undefined) {
        window.DFSignals.registry[id] = true;
    }
    if (window.DFSignals.registry[signal] !== undefined) {
        console.debug('call "' + signal + '"', opts);
        for (let i = 0; i < window.DFSignals.registry[signal].length; i += 1) {
            window.DFSignals.registry[signal][i](opts, id);
        }
    }
    if (id === undefined) {
        console.debug('call from client: "' + signal + '"', opts);
        const msg = JSON.stringify({signal: signal, opts: opts});
        if (window.DFSignals.connection) {
            window.DFSignals.connection.send(msg);
        } else {
            window.DFSignals.buffer.push(msg);
        }
    }

    return false;
}

function connect(signal, fn) {
    /*"""
    .. function:: connect(signal, fn)

        Connect a javascript code to the given signal name.

        :param string signal: Name of the signal.
        :param function fn: Function that takes a single object as argument. The properties of this object are the signal arguments.
        :returns: nothing.
    */
    if (window.DFSignals.registry[signal] === undefined) {
        window.DFSignals.registry[signal] = [];
    }
    window.DFSignals.registry[signal].push(fn);
}

document.addEventListener("DOMContentLoaded", websocketConnect);

window.DFSignals.call = call;
window.DFSignals.connect = connect;
