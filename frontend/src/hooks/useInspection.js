import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api";

const empty = { sensors: [], images: [], fusion: null };

export default function useInspection(followCameraSwitch = false) {
  const [sample, setSample] = useState(null);
  const [data, setData] = useState(empty);
  const [report, setReport] = useState(null);
  const [recent, setRecent] = useState([]);
  const [healthInfo, setHealthInfo] = useState(null);
  const [online, setOnline] = useState(false);
  const [connectionChecked, setConnectionChecked] = useState(false);
  const [active, setActive] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const selected = useRef(null);
  const sequence = useRef(0);
  const follow = useRef(followCameraSwitch);
  follow.current = followCameraSwitch;

  const selectSample = useCallback((row) => {
    selected.current = row?.sample_id || null;
    sequence.current += 1;
    setSample(row);
    setData(empty);
    setReport(null);
    setErr("");
  }, []);

  const refresh = useCallback(async (id = selected.current) => {
    if (!id || id !== selected.current) return;
    const token = ++sequence.current;
    try {
      const [next, summary] = await Promise.all([
        api.bundle(id),
        api.investigation(id),
      ]);
      if (token !== sequence.current || selected.current !== id) return;
      setData(next);
      setReport(summary);
      setSample(next.sample);
      setErr("");
    } catch (error) {
      if (token === sequence.current && selected.current === id) {
        setErr(error.message);
        setReport(null);
        setData((current) => ({ ...current, fusion: null }));
      }
    }
  }, []);

  useEffect(() => {
    let disposed = false;
    let timer;
    const poll = async () => {
      try {
        const h = await api.health();
        if (disposed) return;
        setHealthInfo(h);
        setOnline(true);
        const [rows, target] = await Promise.all([
          api.listSamples(),
          api.activeSample(),
        ]);
        if (disposed) return;
        setRecent(rows);
        setActive(target);
        // Select once on first connection. Never override intentional history browsing.
        if (!selected.current && (target || rows[0]))
          selectSample(target || rows[0]);
      } catch {
        if (!disposed) {
          setHealthInfo(null);
          setOnline(false);
          setReport(null);
          setData((current) => ({ ...current, fusion: null }));
        }
      } finally {
        if (!disposed) {
          setConnectionChecked(true);
          timer = setTimeout(poll, 5000);
        }
      }
    };
    poll();
    return () => {
      disposed = true;
      clearTimeout(timer);
    };
  }, [selectSample]);

  useEffect(() => {
    const id = sample?.sample_id;
    if (!id) return;
    let disposed = false;
    let socket;
    let retry;
    let refreshTimer;
    let inFlight = false;
    let pending = false;
    const update = async () => {
      if (disposed) return;
      if (inFlight) {
        pending = true;
        return;
      }
      inFlight = true;
      await refresh(id);
      inFlight = false;
      if (pending && !disposed) {
        pending = false;
        update();
      }
    };
    const connect = () => {
      if (disposed) return;
      socket = new WebSocket(api.wsUrl(id));
      socket.onmessage = (event) => {
        if (disposed) return;
        let message;
        try {
          message = JSON.parse(event.data);
        } catch {
          return;
        }
        const frame = message.data;
        if (
          follow.current &&
          frame?.auto_detection?.sample_changed &&
          frame.auto_detection.previous_sample_id === selected.current
        ) {
          selectSample({
            sample_id: frame.sample_id,
            fruit_type: frame.fruit_type,
          });
        } else update();
      };
      socket.onclose = () => {
        if (!disposed) retry = setTimeout(connect, 1500);
      };
    };
    update();
    connect();
    // Refresh even without events so evidence expiration is visible.
    refreshTimer = setInterval(update, 5000);
    return () => {
      disposed = true;
      sequence.current += 1;
      clearTimeout(retry);
      clearInterval(refreshTimer);
      if (socket) {
        socket.onclose = null;
        socket.onmessage = null;
        socket.close();
      }
    };
  }, [sample?.sample_id, refresh, selectSample]);

  const create = async (fruit) => {
    setBusy(true);
    setErr("");
    try {
      const row = await api.createSample(fruit);
      selectSample(row);
      setActive(row);
      return row;
    } catch (error) {
      setErr(error.message);
      return null;
    } finally {
      setBusy(false);
    }
  };
  const activate = async () => {
    if (!selected.current) return;
    try {
      setActive(await api.activateSample(selected.current));
    } catch (error) {
      setErr(error.message);
    }
  };
  const onFrame = (result) => {
    if (
      result?.auto_detection?.sample_changed &&
      result.auto_detection.previous_sample_id === selected.current
    ) {
      const row = {
        sample_id: result.sample_id,
        fruit_type: result.fruit_type,
      };
      selectSample(row);
      setActive(row);
    } else refresh();
  };
  return {
    sample,
    data,
    report,
    recent,
    healthInfo,
    online,
    connectionChecked,
    active,
    err,
    busy,
    refresh,
    selectSample,
    create,
    activate,
    onFrame,
    setErr,
  };
}
