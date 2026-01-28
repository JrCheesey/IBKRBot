"""IBKR error code mappings."""


class IBKRErrorCodes:
    # Order errors
    DUPLICATE_ORDER_ID = 103
    ORDER_ID_USED = 104
    PRICE_TOO_FAR = 110
    ORDER_NOT_FOUND = 135
    ORDER_ALREADY_CANCELLED = 136
    CANCEL_NOT_ALLOWED = 161
    NO_SECURITY_FOUND = 200
    PERMISSION_DENIED = 201
    ORDER_CANCELLED = 202
    SERVER_ERROR = 321
    ORDER_REJECTED = 322
    NO_HISTORICAL_DATA = 354
    INVALID_ORDER = 399

    # Connection errors
    CONNECT_FAILED = 502
    NOT_CONNECTED = 504
    CONNECTIVITY_LOST = 1100
    CONNECTIVITY_RESTORED_DATA_LOST = 1101
    CONNECTIVITY_RESTORED = 1102

    # Routing and attribute errors
    ROUTING_ERROR = 10147
    MARGIN_REJECTED = 10148
    ETRADE_ONLY_NOT_SUPPORTED = 10268
    FIRM_QUOTE_ONLY_NOT_SUPPORTED = 10269

    # Warning codes (informational, not errors)
    WARNING_CODES = set(range(2100, 2200))

    # Error code to friendly message mapping
    MESSAGES = {
        103: {
            "title": "Duplicate Order ID",
            "message": "This order ID has already been used.",
            "hint": "Reconnect to IB Gateway to get a fresh order ID sequence."
        },
        104: {
            "title": "Order ID Already Used",
            "message": "This order ID was previously submitted.",
            "hint": "Reconnect to IB Gateway to get a fresh order ID sequence."
        },
        110: {
            "title": "Price Too Far From Market",
            "message": "The order price is too far from the current market price.",
            "hint": "Adjust your entry price to be closer to the current market."
        },
        135: {
            "title": "Order Not Found",
            "message": "Cannot find order with the specified ID.",
            "hint": "The parent order may have been rejected. Check for other error messages."
        },
        136: {
            "title": "Order Already Cancelled",
            "message": "This order has already been cancelled.",
            "hint": "Refresh your order list to see current status."
        },
        161: {
            "title": "Cannot Cancel Order",
            "message": "The order is not in a cancellable state.",
            "hint": "The order may have already been filled or cancelled."
        },
        200: {
            "title": "Security Not Found",
            "message": "No security definition found for this symbol.",
            "hint": "Check that the symbol is correct and includes the right exchange."
        },
        201: {
            "title": "Permission Denied",
            "message": "API not enabled or account permissions insufficient.",
            "hint": "Enable API access in TWS/Gateway settings, or check account permissions."
        },
        202: {
            "title": "Order Cancelled",
            "message": "The order was cancelled.",
            "hint": "Order cancellation was processed successfully."
        },
        321: {
            "title": "Server Error",
            "message": "IBKR server encountered an error.",
            "hint": "Wait a moment and try again. If persistent, check IBKR system status."
        },
        322: {
            "title": "Order Rejected",
            "message": "The order was rejected by IBKR.",
            "hint": "Check the error details for specific rejection reason."
        },
        354: {
            "title": "No Historical Data Permissions",
            "message": "You don't have permissions for historical data.",
            "hint": "Subscribe to market data or use delayed data settings."
        },
        399: {
            "title": "Invalid Order",
            "message": "Order parameters are invalid or not allowed.",
            "hint": "Check order type, quantity, price levels, and account settings."
        },
        502: {
            "title": "Connection Failed",
            "message": "Could not connect to TWS/Gateway.",
            "hint": "Ensure TWS or IB Gateway is running and API is enabled on the correct port."
        },
        504: {
            "title": "Not Connected",
            "message": "No connection to TWS/Gateway.",
            "hint": "Click Connect to establish connection to IB Gateway."
        },
        1100: {
            "title": "Connectivity Problem",
            "message": "Connection to IBKR servers was lost.",
            "hint": "Check your internet connection. Will attempt to reconnect automatically."
        },
        1101: {
            "title": "Connectivity Restored",
            "message": "Connection restored but some data may have been lost.",
            "hint": "Refresh your orders and positions to ensure you have current data."
        },
        1102: {
            "title": "Connectivity Restored",
            "message": "Connection restored with data maintained.",
            "hint": "You may continue trading normally."
        },
        10147: {
            "title": "Product Routing Error",
            "message": "Product not available or cannot be routed.",
            "hint": "Canadian ETFs may not be available in paper trading. Try a different symbol or switch to live (with caution)."
        },
        10148: {
            "title": "Margin Rejected",
            "message": "Order rejected due to margin requirements.",
            "hint": "Reduce position size or ensure sufficient margin in your account."
        },
        10268: {
            "title": "Unsupported Order Attribute",
            "message": "The 'EtradeOnly' order attribute is not supported.",
            "hint": "This should be handled automatically. If you see this error, please report it."
        },
        10269: {
            "title": "Unsupported Order Attribute",
            "message": "The 'FirmQuoteOnly' order attribute is not supported.",
            "hint": "This should be handled automatically. If you see this error, please report it."
        },
    }

    @staticmethod
    def get_friendly_message(error_code: int, default_msg: str = "") -> dict:
        if error_code in IBKRErrorCodes.MESSAGES:
            return IBKRErrorCodes.MESSAGES[error_code]

        return {
            "title": "IBKR Error",
            "message": default_msg or f"Error code {error_code}",
            "hint": "Check IBKR logs for more details."
        }

    @staticmethod
    def is_warning(error_code: int) -> bool:
        return error_code in IBKRErrorCodes.WARNING_CODES

    @staticmethod
    def is_critical_error(error_code: int) -> bool:
        critical_codes = {
            IBKRErrorCodes.PERMISSION_DENIED,
            IBKRErrorCodes.ROUTING_ERROR,
            IBKRErrorCodes.CONNECT_FAILED,
            IBKRErrorCodes.NOT_CONNECTED,
            IBKRErrorCodes.CONNECTIVITY_LOST,
            IBKRErrorCodes.NO_SECURITY_FOUND,
            IBKRErrorCodes.MARGIN_REJECTED,
        }
        return error_code in critical_codes

    @staticmethod
    def is_order_rejection(error_code: int) -> bool:
        rejection_codes = {
            IBKRErrorCodes.PERMISSION_DENIED,
            IBKRErrorCodes.ORDER_REJECTED,
            IBKRErrorCodes.INVALID_ORDER,
            IBKRErrorCodes.MARGIN_REJECTED,
            IBKRErrorCodes.ROUTING_ERROR,
            IBKRErrorCodes.NO_SECURITY_FOUND,
            IBKRErrorCodes.PRICE_TOO_FAR,
        }
        return error_code in rejection_codes
