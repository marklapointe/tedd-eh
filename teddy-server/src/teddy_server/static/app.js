/* SPDX-License-Identifier: BSD-3-Clause */
/* Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org> */
/* See LICENSE file for full license text. */

(function() {
    'use strict';

    const WS_URL = `ws://${window.location.host}/ws/operator`;
    let ws = null;
    let selectedDollId = null;
    const dolls = new Map();

    // DOM elements
    const connectionStatus = document.getElementById('connection-status');
    const dollList = document.getElementById('doll-list');
    const selectedDollInfo = document.getElementById('selected-doll-info');
    const controls = document.getElementById('controls');
    const conversationLog = document.getElementById('conversation-log');
    const videoContainer = document.getElementById('video-container');
    const messageText = document.getElementById('message-text');
    const servoAngle = document.getElementById('servo-angle');
    const servoAngleDisplay = document.getElementById('servo-angle-display');

    function connect() {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            connectionStatus.textContent = 'Connected';
            connectionStatus.classList.add('connected');
        };

        ws.onclose = () => {
            connectionStatus.textContent = 'Disconnected';
            connectionStatus.classList.remove('connected');
            setTimeout(connect, 3000);
        };

        ws.onerror = (err) => {
            console.error('WebSocket error:', err);
        };

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                handleMessage(msg);
            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        };
    }

    function handleMessage(msg) {
        switch (msg.type) {
            case 'doll_list':
                updateDollList(msg.dolls);
                break;
            case 'doll_connected':
                fetchDolls();
                break;
            case 'doll_disconnected':
                dolls.delete(msg.doll_id);
                if (selectedDollId === msg.doll_id) {
                    selectedDollId = null;
                    updateSelectedDoll();
                }
                renderDollList();
                break;
            case 'doll_status':
                if (dolls.has(msg.doll_id)) {
                    dolls.get(msg.doll_id).status = msg.status;
                    renderDollList();
                }
                break;
            case 'sensor_data':
                if (dolls.has(msg.doll_id)) {
                    const doll = dolls.get(msg.doll_id);
                    if (msg.data.battery !== undefined) doll.battery = msg.data.battery;
                    if (msg.data.wifi_rssi !== undefined) doll.wifi_rssi = msg.data.wifi_rssi;
                    renderDollList();
                }
                break;
            case 'conversation':
                addConversationMessage(msg.doll_id, msg.role, msg.text);
                break;
            case 'video_frame':
                if (selectedDollId === msg.doll_id) {
                    updateVideoFeed(msg.data);
                }
                break;
            case 'audio_chunk':
                // Audio monitoring could be implemented here
                break;
        }
    }

    function fetchDolls() {
        fetch('/api/dolls')
            .then(r => r.json())
            .then(data => updateDollList(data))
            .catch(err => console.error('Failed to fetch dolls:', err));
    }

    function updateDollList(dollData) {
        dolls.clear();
        for (const d of dollData) {
            dolls.set(d.id, d);
        }
        renderDollList();
    }

    function renderDollList() {
        if (dolls.size === 0) {
            dollList.innerHTML = '<p class="empty-state">No dolls connected</p>';
            return;
        }

        dollList.innerHTML = '';
        for (const [id, doll] of dolls) {
            const card = document.createElement('div');
            card.className = 'doll-card' + (id === selectedDollId ? ' selected' : '');
            card.dataset.dollId = id;

            const telemetry = [];
            if (doll.battery !== null && doll.battery !== undefined) {
                telemetry.push(`Battery: ${doll.battery.toFixed(1)}%`);
            }
            if (doll.wifi_rssi !== null && doll.wifi_rssi !== undefined) {
                telemetry.push(`WiFi: ${doll.wifi_rssi} dBm`);
            }

            card.innerHTML = `
                <div class="doll-name">${escapeHtml(doll.name)}</div>
                <div class="doll-status">Status: ${doll.status}</div>
                ${telemetry.length > 0 ? `<div class="doll-telemetry">${telemetry.join(' | ')}</div>` : ''}
            `;

            card.addEventListener('click', () => selectDoll(id));
            dollList.appendChild(card);
        }
    }

    function selectDoll(id) {
        selectedDollId = id;
        renderDollList();
        updateSelectedDoll();
    }

    function updateSelectedDoll() {
        if (!selectedDollId || !dolls.has(selectedDollId)) {
            selectedDollInfo.innerHTML = '<p class="empty-state">Select a doll to control</p>';
            controls.classList.add('hidden');
            videoContainer.innerHTML = '<p class="empty-state">No video feed</p>';
            return;
        }

        const doll = dolls.get(selectedDollId);
        selectedDollInfo.innerHTML = `
            <div class="doll-card selected">
                <div class="doll-name">${escapeHtml(doll.name)}</div>
                <div class="doll-status">Status: ${doll.status}</div>
            </div>
        `;
        controls.classList.remove('hidden');
    }

    function addConversationMessage(dollId, role, text) {
        if (selectedDollId !== dollId) return;

        const msg = document.createElement('div');
        msg.className = `message ${role}`;
        msg.innerHTML = `
            <div class="role">${role}</div>
            <div class="text">${escapeHtml(text)}</div>
        `;
        conversationLog.appendChild(msg);
        conversationLog.scrollTop = conversationLog.scrollHeight;
    }

    function updateVideoFeed(data) {
        videoContainer.innerHTML = `<img src="data:image/jpeg;base64,${data}" alt="Video feed">`;
    }

    function sendMessage() {
        if (!selectedDollId || !ws) return;
        const text = messageText.value.trim();
        if (!text) return;

        ws.send(JSON.stringify({
            type: 'text_message',
            doll_id: selectedDollId,
            text: text,
        }));

        addConversationMessage(selectedDollId, 'user', text);
        messageText.value = '';
    }

    function sendServoCommand() {
        if (!selectedDollId || !ws) return;
        const channel = parseInt(document.getElementById('servo-channel').value, 10);
        const angle = parseInt(servoAngle.value, 10);

        ws.send(JSON.stringify({
            type: 'servo_command',
            doll_id: selectedDollId,
            channel: channel,
            angle: angle,
            speed_ms: 100,
        }));
    }

    function sendExpression(name) {
        if (!selectedDollId || !ws) return;
        ws.send(JSON.stringify({
            type: 'expression',
            doll_id: selectedDollId,
            name: name,
        }));
    }

    function sendAction(name) {
        if (!selectedDollId || !ws) return;
        ws.send(JSON.stringify({
            type: 'action',
            doll_id: selectedDollId,
            name: name,
        }));
    }

    function stopSpeaking() {
        if (!selectedDollId || !ws) return;
        ws.send(JSON.stringify({
            type: 'stop_speaking',
            doll_id: selectedDollId,
        }));
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Event listeners
    document.getElementById('send-message').addEventListener('click', sendMessage);
    document.getElementById('send-servo').addEventListener('click', sendServoCommand);
    document.getElementById('stop-speaking').addEventListener('click', stopSpeaking);

    servoAngle.addEventListener('input', () => {
        servoAngleDisplay.textContent = servoAngle.value;
    });

    document.querySelectorAll('.expr-btn').forEach(btn => {
        btn.addEventListener('click', () => sendExpression(btn.dataset.expr));
    });

    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => sendAction(btn.dataset.action));
    });

    messageText.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Initialize
    connect();
    fetchDolls();
})();
