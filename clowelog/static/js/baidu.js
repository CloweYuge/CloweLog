/**
 * Created by Administrator on 2018/12/16.
 */
s.a.createElement("div", {
    className: "tags-container " + (this.state.focus ? "focus": ""),
    onClick: function() {
        e.input.focus(),
        e.setState({
            focus: !0
        })
    }
},
n && n.map(function(t, n) {
    var a = t + n;
    return s.a.createElement("div", {
        key: a,
        className: "tag-item"
    },
    s.a.createElement("span", null, t), s.a.createElement("span", {
        className: "remove",
        onClick: function() {
            e.onRemoveTag(t, n)
        }
    },
    "\xd7"))
}),
    s.a.createElement("input", {
    ref: function(t) {
        e.input = t
    },
    placeholder: this.state.placeholder,
    value: this.state.text,
    disabled: this.state.disabled,
    onChange: this.handleInputChange,
    onKeyDown: this.handleKeyDown,
    onBlur: function() {
        e.setState({
            focus: !1
        })
    }
}))

// s.a.createElement("div",{className:"tags-container "+(this.state.focus?"focus":""),onClick:function(){e.input.focus(),e.setState({focus:!0})}},n&&n.map(function(t,n){var a=t+n;return s.a.createElement("div",{key:a,className:"tag-item"},s.a.createElement("span",null,t),s.a.createElement("span",{className:"remove",onClick:function(){e.onRemoveTag(t,n)}},"\xd7"))}),s.a.createElement("input",{ref:function(t){e.input=t},placeholder:this.state.placeholder,value:this.state.text,disabled:this.state.disabled,onChange:this.handleInputChange,onKeyDown:this.handleKeyDown,onBlur:function(){e.setState({focus:!1})}}))
// this.props.maxCount?s.a.createElement("div",{className:"remind"},"\u60a8\u53ef\u6dfb\u52a0",s.a.createElement("span",{className:"count"},this.props.maxCount,"\u4e2a\u6807\u7b7e"),"\uff0c\u6309\u56de\u8f66\u952e\u786e\u8ba4\u3002\u63cf\u8ff0\u8d8a\u51c6\u786e\uff0c\u8d8a\u5229\u4e8e\u89e6\u8fbe\u5174\u8da3\u4eba\u7fa4\u3002")