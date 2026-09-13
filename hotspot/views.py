from django.shortcuts import render


def portal(request):
    context = {
        "client_mac": request.GET.get("clientMac", ""),
        "client_ip": request.GET.get("clientIp", ""),
        "ap_mac": request.GET.get("apMac", ""),
        "ssid_name": request.GET.get("ssidName", ""),
        "radio_id": request.GET.get("radioId", ""),
        "site": request.GET.get("site", ""),
        "redirect_url": request.GET.get("redirectUrl", ""),
    }

    return render(
        request,
        "hotspot/portal.html",
        context,
    )