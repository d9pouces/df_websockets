/******************************************************************************
 * This file is part of Interdiode                                            *
 *                                                                            *
 * Copyright (C) 2020 Matthieu Gallet <matthieu.gallet@19pouces.net>          *
 * All Rights Reserved                                                        *
 *                                                                            *
 ******************************************************************************/

DFSignals = {
    connection: null,
    buffer: [],
    registry: {},
    wsurl: null
};

function getCookie(cname) {
    const name = cname + "=";
    console.info(document.cookie);
    const decodedCookie = decodeURIComponent(document.cookie);
    console.info(decodedCookie);
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
    if (DFSignals.wsurl === null) {
        const dfWsURL = getCookie("dfwsurl");
        console.info(dfWsURL);
        DFSignals.wsurl = decodeURIComponent(dfWsURL);
        console.warn(DFSignals.wsurl);
    }
    const connection = new WebSocket(DFSignals.wsurl);
    /* cannot use header or cookies (cookies may change after the initial connection)
    *  so we use GET parameter
    *  */
    connection.onopen = () => {
        DFSignals.connection = connection;
        for (let i = 0; i < DFSignals.buffer.length; i++) {
            connection.send(DFSignals.buffer[i]);
        }
        DFSignals.buffer = [];
    };
    connection.onmessage = (e) => {
        console.debug('received call ' + e.data + ' from server.')
        const msg = JSON.parse(e.data);
        // noinspection JSUnresolvedVariable
        if (msg.signal && msg.signal_id) {
            DFSignals.call(msg.signal, msg.opts, msg.signal_id);
        }
    };
    connection.onerror = (e) => {
        console.error("WS error: " + e);
    };
    connection.onclose = () => {
        DFSignals.connection = null;
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
    // if (DFSignals.registry[signal] === undefined) {
    //     console.debug('unknown call "' + signal + '" (from both client and server).');
    //     return false;
    // } else
    if ((id !== undefined) && (DFSignals.registry[id] !== undefined)) {
        return false;
    } else if (id !== undefined) {
        DFSignals.registry[id] = true;
    }
    if (DFSignals.registry[signal] !== undefined) {
        console.debug('call "' + signal + '"', opts);
        for (let i = 0; i < DFSignals.registry[signal].length; i += 1) {
            DFSignals.registry[signal][i](opts, id);
        }
    }
    if (id === undefined) {
        console.debug('call from client: "' + signal + '"', opts);
        const msg = JSON.stringify({signal: signal, opts: opts});
        if (DFSignals.connection) {
            DFSignals.connection.send(msg);
        } else {
            DFSignals.buffer.push(msg);
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
    if (DFSignals.registry[signal] === undefined) {
        DFSignals.registry[signal] = [];
    }
    DFSignals.registry[signal].push(fn);
}

document.addEventListener("DOMContentLoaded", websocketConnect);

DFSignals.call = call;
DFSignals.connect = connect;
