from django.shortcuts import render


def portal(request):
    """
    External Portal landing page.

    Omada sends the connected client's information
    as query parameters. We pass those values to
    the portal template so they can be carried through
    the purchase process.
    """

    context = {
        "client_mac": request.GET.get("clientMac", ""),
        "client_ip": request.GET.get("clientIp", ""),
        "ap_mac": request.GET.get("apMac", ""),
        "gateway_mac": request.GET.get("gatewayMac", ""),
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

