$(document).ready(function () {
    // Lesson Completion Form Submission
    $("#lesson-form").submit(function (event) {
        event.preventDefault();
        var selectedLesson = $("#lesson-select").val();

        $.ajax({
            url: "/complete_lesson",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ lesson: selectedLesson }),
            success: function (response) {
                $("#status-message").text(response.message).css("color", "green");
                $("#completed-lessons").append("<li>" + selectedLesson + "</li>");
                $("#lesson-select option[value='" + selectedLesson + "']").remove();
                $("#recommendations-list li").filter(function () {
                    return $(this).text() === selectedLesson;
                }).remove();

                // Fetch new recommendations
                $.get("/get_recommendations", function (data) {
                    $("#recommendations-list, #lesson-select").empty();
                    data.recommendations.forEach(function (lesson) {
                        $("#recommendations-list").append("<li>" + lesson + "</li>");
                        $("#lesson-select").append("<option value='" + lesson + "'>" + lesson + "</option>");
                    });
                });
            },
            error: function (response) {
                $("#status-message").text(response.responseJSON.error).css("color", "red");
            }
        });
    });

    // AI Tutor Chat Functionality
    var socket = io();

    $("#sendBtn").click(function () {
        sendMessage();
    });

    $("#chatInput").keypress(function (event) {
        if (event.which === 13) { // Enter key pressed
            sendMessage();
        }
    });

    function sendMessage() {
        var message = $("#chatInput").val().trim();
        if (message) {
            $("#messages").append("<p><b>You:</b> " + message + "</p>");
            socket.emit("message", { message: message });
            $("#chatInput").val("");
        }
    }

    socket.on("response", function (data) {
        var responseText = data.message;
        $("#messages").append("<p><b>AI Tutor:</b> " + responseText + "</p>");
        speak(responseText); // Text-to-Speech (TTS) for AI responses
    });

    // Voice Recognition
    $("#voiceBtn").click(function () {
        var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-US';
        recognition.start();

        recognition.onresult = function (event) {
            var speechResult = event.results[0][0].transcript;
            $("#chatInput").val(speechResult);
            sendMessage();
        };

        recognition.onerror = function (event) {
            alert("Speech recognition error: " + event.error);
        };
    });

    // Text-to-Speech (TTS)
    function speak(text) {
        var speech = new SpeechSynthesisUtterance(text);
        speech.lang = 'en-US';
        window.speechSynthesis.speak(speech);
    }
});
