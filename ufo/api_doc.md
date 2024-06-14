# UFO API Status Documentation

## Status Definitions and Descriptions

### 1. AWAITING
- **Description:** The system is waiting for the UFO instance to start.
- **Available Methods:** `start_ufo`, `get_status`
- **Exceptions:** Attempting to call `handle_request`, `get_session_state`, `pause_ufo`, `resume_ufo`, or `confirmation` will result in an "UFO not running" message.

### 2. WAITINGREQUEST
- **Description:** The UFO instance has started and is waiting for a request from the user.
- **Available Methods:** `handle_request`,  `get_status`, `get_session_state`, 
- **Exceptions:** Attempting to call `start_ufo` will result in an "UFO instance already running" message. Attempting to call `pause_ufo` will result in a "No session running" message.

### 3. RUNNING
- **Description:** The UFO instance is currently processing a request.
- **Available Methods:** `get_status`, `get_session_state`, `pause_ufo`, `resume_ufo`
- **Exceptions:** Attempting to call `handle_request`, `start_ufo`, or `confirmation` will result in a "No request expected" message.

### 4. CONFIRMATION
- **Description:** The UFO instance is waiting for user confirmation to proceed.
- **Available Methods:** `confirmation`, `get_status`
- **Exceptions:** Attempting to call `handle_request`, `start_ufo`, `get_session_state`, or `pause_ufo` will result in a "No request expected" message.

### 5. COMPLETED
- **Description:** The UFO task is completed.
- **Available Methods:** `start_ufo`
- **Exceptions:** Attempting to call `handle_request`, `get_status`, `get_session_state`, `pause_ufo`, `resume_ufo`, or `confirmation` will result in a "UFO not running" message.

### 6. ERROR
- **Description:** An error has occurred in the UFO instance.
- **Available Methods:** `get_status`
- **Exceptions:** Attempting to call any other methods will result in a relevant error message.

### 7. ROUNDFINISHED
- **Description:** A round of the task has finished and is awaiting evaluation or the next step.
- **Available Methods:** `handle_request`, `confirmation`, `get_status`
- **Exceptions:** Attempting to call `start_ufo` will result in an "UFO instance already running" message.

### 8. EVALUATING
- **Description:** The UFO instance is evaluating the results of the completed task.
- **Available Methods:** `get_status`
- **Exceptions:** Attempting to call `handle_request`, `start_ufo`, `get_session_state`, `pause_ufo`, or `confirmation` will result in a "No request expected" or "UFO instanca already running" message.

### 9. SAVEEXP
- **Description:** The UFO instance is saving the experimental data or results.
- **Available Methods:** `get_status`, `confirmation`
- **Exceptions:** Attempting to call any other methods will result in a relevant error message.

### 10. PAUSED
- **Description:** The UFO instance is paused.
- **Available Methods:** `resume_ufo`, `get_status`
- **Exceptions:** Attempting to call `handle_request`, `start_ufo`, `get_session_state`, `pause_ufo`, or `confirmation` will result in a "Session paused" message.

### 11. NEEDLOGIN
- **Description:** The UFO instance requires user login.
- **Available Methods:** `get_status`
- **Exceptions:** Attempting to call any other methods will result in a relevant error message.

## Summary of Methods and Status

Here's a quick reference to see which methods are available in each status:

| Status          | Available Methods                                                                                                                                  |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| AWAITING        | `start_ufo`                                                                                                                                         |
| WAITINGREQUEST  | `handle_request`, `get_status`, `get_session_state`, `pause_ufo`, `confirmation`                                 |
| RUNNING         | `get_status`, `get_session_state`, `pause_ufo`                                                                  |
| CONFIRMATION    | `confirmation`, `get_status`                                                                                                                        |
| COMPLETED       | `handle_request`, `get_status`, `get_session_state`, `pause_ufo`, `confirmation`                                 |
| ERROR           | `get_status`                                                                                                                                       |
| ROUNDFINISHED   | `handle_request`, `confirmation`, `get_status`                                                                                                      |
| EVALUATING      | `get_status`                                                                                                                                       |
| SAVEEXP         | `get_status`, `confirmation`                                                                                                                        |
| PAUSED          | `resume_ufo`, `get_status`                                                                                                                          |
| NEEDLOGIN       | `get_status`                                                                                                                                       |

## API Endpoints Documentation

### `start_ufo`
- **Endpoint:** `/ufo/start`
- **Method:** POST
- **Request Body:**
    ```json
    {
        "task": "your_task_name"
    }
    ```
- **Response:**
    ```json
    {
        "status": "WAITINGREQUEST",
        "message": "UFO instance started",
        "data": null
    }
    ```

### `handle_request`
- **Endpoint:** `/ufo/request`
- **Method:** POST
- **Request Body:**
    ```json
    {
        "request": "Open outlook and initiate an email to Peter."
    }
    ```
- **Response:**
    ```json
    {
        "status": "EVALUATING",
        "message": "Round finished. Evaluating...",
        "data": null
    }
    ```


### `get_status`
- **Endpoint:** `/ufo/get_status`
- **Method:** GET
- **Response:**
    ```json
    {
        "status": "ROUNDFINISHED",
        "message": "Here is the comment for the last request. Please enter your new request. Enter 'N' for exit.",
        "data": {
            "response": "Comment💬: The user request is 'Nothing', so no further action is required."
        }
    }
    ```

### `get_session_state`
- **Endpoint:** `/ufo/get_session_state`
- **Method:** GET
- **Response:**
    ```json
    {
        "status": "RUNNING",
        "message": null,
        "data": {"key": "value"}
    }
    ```

### `pause_ufo`
- **Endpoint:** `/ufo/pause`
- **Method:** GET
- **Response:**
    ```json
    {
        "status": "PAUSED",
        "message": "Session paused",
        "data": null  
    }
    ```

### `resume_ufo`
- **Endpoint:** `/ufo/resume`
- **Method:** GET
- **Response:**
    ```json
    {
        "status": "RUNNING",
        "message": "Session resumed",
        "data": null  
    }
    ```

### `confirmation`
- **Endpoint:** `/ufo/confirmation`
- **Method:** POST
- **Request Body:**
    ```json
    {
        "confirmation": "Y"
    }
    ```
- **Response:**
    ```json
    {
        "status": "RUNNING",
        "message": "Confirmation received",
        "data": null
    }
    ```
