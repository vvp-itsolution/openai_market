function insertAtCursor(value) {
    textarea = document.getElementById('textarea1');

    if (textarea.selectionStart || textarea.selectionStart == '0') {
        var startPos = textarea.selectionStart;
        var endPos = textarea.selectionEnd;
        textarea.value = textarea.value.substring(0, startPos) + value + textarea.value.substring(endPos, textarea.value.length);
        setCursorAt(textarea, startPos, endPos);
    } else {
        textarea.value += value;
    }

}


function setCursorAt(textarea, start, end) {
    textarea.setSelectionRange(start, end);
}


function insertImageMarkdown(url) {
    var value = '![img]' + '(' + url + ')'
    insertAtCursor(value);
}
