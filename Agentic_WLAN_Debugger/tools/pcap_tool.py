# tools/pcap_tool.py

import pyshark
import asyncio

def parse_pcap(file_path: str):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    capture = pyshark.FileCapture(file_path)

    packets = []
    
    try:
        for i, pkt in enumerate(capture):
            try:
                # ── time ──────────────────────────────────────────
                time_val = str(pkt.sniff_time)

                # ── length (frame layer is always present) ─────────
                try:
                    length = int(pkt.length)
                except Exception:
                    length = 0

                # ── protocol ──────────────────────────────────────
                try:
                    protocol = pkt.highest_layer
                except Exception:
                    protocol = None

                # ── WLAN layer fields ──────────────────────────────
                wlan = getattr(pkt, "wlan", None)
                src         = getattr(pkt.wlan, "sa", None) if hasattr(pkt, "wlan") else None
                dst         = getattr(pkt.wlan, "da", None) if hasattr(pkt, "wlan") else None
                retry       = getattr(wlan, "fc_retry", "0")
                seq_num     = getattr(wlan, "seq", None)
                frame_type  = getattr(wlan, "fc_type", None)
                frame_sub   = getattr(wlan, "fc_subtype", None)

                # ── Radiotap (signal strength) ─────────────────────
                radiotap = getattr(pkt, "radiotap", None)
                rssi = getattr(radiotap, "dbm_antsignal", None)

                # ── fallback src/dst from IP/ETH if no WLAN ────────
                if src is None:
                    ip = getattr(pkt, "ip", None)
                    src = getattr(ip, "src", None)
                if dst is None:
                    ip = getattr(pkt, "ip", None)
                    dst = getattr(ip, "dst", None)

                packets.append({
                    "time":             time_val,
                    "src":              src,
                    "dst":              dst,
                    "protocol":         protocol,
                    "length":           length,
                    "retry":            retry,
                    "sequence_number":  seq_num,
                    "frame_type":       frame_type,
                    "frame_subtype":    frame_sub,
                    "rssi":             rssi,
                })

            except Exception as e1:
                print(f"[ERROR] Packet {i}: {e1}")

    except Exception as e2:
        print(f"TShark error handled safely: {e2}")

    finally:
        try:
            capture.close()
        except Exception:
            pass
    return packets

#print("================================================================")
#print(parse_pcap('E:\\Gen AI\\Wireshark AI\\test_dataset\\test.pcap'))