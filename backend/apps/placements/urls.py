"""URL patterns for Placement Management and Offers (MOD-009)."""
from django.urls import path
from apps.placements.views import (
    PlacementOfferListCreateAPIView,
    PlacementOfferDetailAPIView,
    PlacementOfferDecisionAPIView,
    PlacementOfferJoiningVerifyAPIView,
)

app_name = "placements"

urlpatterns = [
    path("offers/", PlacementOfferListCreateAPIView.as_view(), name="offer_list_create"),
    path("offers/<uuid:id>/", PlacementOfferDetailAPIView.as_view(), name="offer_detail"),
    path("offers/<uuid:id>/decision/", PlacementOfferDecisionAPIView.as_view(), name="offer_decision"),
    path("offers/<uuid:id>/verify-joining/", PlacementOfferJoiningVerifyAPIView.as_view(), name="offer_verify_joining"),
]

