# tools/pcap_tool.py

import pyshark
import asyncio

def parse_pcap(file_path: str):

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    capture = pyshark.FileCapture(
        file_path,
        keep_packets=False,
        only_summaries=True,
        include_raw=False,
        use_json=False,   # IMPORTANT: reduces crash risk
        tshark_path=None
    )

    packets = []

    try:
        for i, pkt in enumerate(capture):
            if i > 2000:
                break
            try:
                packet_info = {
                    "time": str(getattr(pkt, "sniff_time", "")),
                    "src": (
                        getattr(getattr(pkt, "wlan", None), "sa", None)
                        if hasattr(pkt, "wlan")
                        else None
                    ),
                    "dst": (
                        getattr(getattr(pkt, "wlan", None), "da", None)
                        if hasattr(pkt, "wlan")
                        else None
                    ),
                    "protocol": getattr(pkt, "highest_layer", None),
                    "length": (
                        int(getattr(pkt, "length", 0))
                        if str(getattr(pkt, "length", "0")).isdigit()
                        else 0
                    ),
                    "retry": (
                        getattr(getattr(pkt, "wlan", None), "fc_retry", 0)
                        if hasattr(pkt, "wlan")
                        else 0
                    ),
                    "sequence_number": (
                        getattr(getattr(pkt, "wlan", None), "seq", None)
                        if hasattr(pkt, "wlan")
                        else None
                    ),
                    "frame_type": (
                        getattr(getattr(pkt, "wlan", None), "fc_type", None)
                        if hasattr(pkt, "wlan")
                        else None
                    ),
                    "frame_subtype": (
                        getattr(getattr(pkt, "wlan", None), "fc_subtype", None)
                        if hasattr(pkt, "wlan")
                        else None
                    ),
                    "rssi": (
                        getattr(getattr(pkt, "radiotap", None), "dbm_antsignal", None)
                        if hasattr(pkt, "radiotap")
                        else None
                    ),
                }

                packets.append(packet_info)

            except Exception:
                continue
    except Exception as e:
        print("TShark error handled safely:", e)

    finally:
        try:
            capture.close()
        except Exception:
            pass

    return packets