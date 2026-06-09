from __future__ import annotations


def _normalize_time(value):
    return " ".join(str(value or "").lower().replace("–", "-").split())


def evaluate_contract_flow(evidence):
    """Classify contract receipt, deposit state, and next follow-up from evidence."""
    signed_received = bool(evidence.get("signed_contract_received"))
    deposit_received = bool(evidence.get("deposit_received"))
    test_requested = bool(evidence.get("test_payment_requested"))
    test_confirmed = bool(evidence.get("test_payment_confirmed"))

    review_codes = []
    contract_time = _normalize_time(evidence.get("contract_time"))
    email_time = _normalize_time(evidence.get("email_time"))
    if contract_time and email_time and contract_time != email_time:
        review_codes.append("TIME_MISMATCH_REVIEW")

    if signed_received:
        contract_status = "signed_received"
    else:
        contract_status = "awaiting_signature"

    if deposit_received:
        deposit_status = "deposit_received"
        next_follow_up_state = "return_fully_signed_copy"
    elif test_requested and test_confirmed:
        deposit_status = "awaiting_deposit"
        next_follow_up_state = "waiting_on_client_deposit"
    elif test_requested:
        deposit_status = "test_payment_pending"
        next_follow_up_state = "confirm_test_payment"
    else:
        deposit_status = "deposit_pending"
        next_follow_up_state = "request_deposit"

    return {
        "contract_status": contract_status,
        "deposit_status": deposit_status,
        "next_follow_up_state": next_follow_up_state,
        "review_codes": review_codes,
        "is_locked_for_accounting": signed_received and deposit_received,
    }
