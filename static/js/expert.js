(function() {
	var modal = undefined;
	
	function showModal(content){
		var HTML = `<div class="modal fade" id="confirmation-modal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&#x1F5D9;</span></button>
        <h4 class="modal-title" id="myModalLabel">&nbsp;</h4>
      </div>
      <div class="modal-body">
        Body
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default btn-cancel" data-dismiss="modal">&#x1F5D9;</button>
        <button type="button" class="btn btn-danger btn-confirm">&checkmark;</button>
      </div>
    </div>
  </div>
</div>`;
		if(modal === undefined) {
			modal = $(HTML);
			modal.action = function(){};
			modal.appendTo("body");
			$(modal.get(0)).find(".modal-footer .btn-confirm").click(function(){
				modal.action();
				modal.modal("hide");
			});
		}
		var m = $(modal.get(0));
		m.find(".modal-body").text($(content).attr("data-confirm"));
		var reply = $(content).attr("data-reply").split(",");
		m.find(".modal-footer .btn-cancel").text(reply[0]);
		m.find(".modal-footer .btn-confirm").text(reply[1]);
		modal.action=function(){
			content.confirmed=true;
			$(content).click();
		};
		modal.modal("show");
	}
	function initConfirm() {
		$(".btn-confirm").click(function(){
			if(this.confirmed === true){
				return true;
			}
			showModal(this);
			return false;
		});
	}
	function showExpert(isExpert)
	{
	  var elements = document.getElementsByClassName("expert");
	  for(var i = 0; elements.length > i; i++)
	  {
	    if(!isExpert) {
	    	elements[i].setAttribute("class","expert experthidden");
	    } else {
	    	elements[i].setAttribute("class","expert");
	    }
	  }
	}
	function initCertForm() {
		if(document.getElementById("placeholderName") == null) {
			return;
		}
		function getHint(id){
			var elem = document.getElementById(id);
			if(elem === null) {
				return null;
			}
			return $(elem).text();
		}
		$("select[name=profile]").off("change");
		$("textarea[name=SANs]").off("keydown");
		$("textarea[name=SANs]").get(0).modified=false;
		$("input[name=CN]").off("keydown");
		$("input[name=CN]").get(0).modified=false;

		var placeholderName = getHint("placeholderName");
		var defaultName = getHint("defaultName");
		var defaultEmail = getHint("defaultEmail");
		var defaultDomain = getHint("defaultDomain");
		if(defaultName === null) {
			return;
		}
		$("textarea[name=SANs]").on("keydown", function(){
			this.modified = this.value !== "";
		});
		$("input[name=CN]").on("keydown", function(){
			this.modified = this.value !== "";
		});

		var loginCheck = document.getElementById("login");
		$("select[name=profile]").change(function(){
			var val = this.value;
			var sans = $("textarea[name=SANs]").get(0);
			if(val.match(/client.*/)) {
				loginCheck.checked = true;
				loginCheck.disabled = false;
			} else {
				loginCheck.checked = false;
				loginCheck.disabled = true;
			}
			if(val.match(/client.*|mail.*/)) {
				if(!sans.modified) {
					sans.value = "email:"+defaultEmail;
				}
			} else if(val.match(/server.*/)) {
				if(!sans.modified) {
					sans.value = defaultDomain === null ? "" : "dns:" + defaultDomain;
				}
			}
			var cn = $("input[name=CN]").get(0);
			if(val.match(/.*-a/)) {
				if(!cn.modified) {
					cn.value = defaultName;
				}
			}else{
				if(!cn.modified) {
					cn.value = placeholderName;
				}
			}
		});
		var children = $("select[name=profile]").get(0).children;
		var target = "client-mail";
		for(var i=0; i < children.length; i++){
			if(children[i].value == "client-mail-a"){
				target = "client-mail-a";
			}
		}

		$("select[name=profile]").get(0).value = target;
		$("select[name=profile]").trigger("change");

	}
	function init(){
		showExpert(false);
		initCertForm();
		var expert = document.getElementById("expertbox");
		if(expert !== null) {
			expert.onchange = (function(expert){return function(){showExpert(expert.checked)}})(expert);
		}
		$(".card-activatable").map(function() {
			var card = $(this);
			var refresh = function(){
				var radio = this.type == "radio";
				if(radio && this.form.currentRadios === undefined) {
					this.form.currentRadios = {};
				}
				if(this.checked) {
					card.find(".card-body").removeClass("d-none");
					if(radio) {
						var rds = this.form.currentRadios;
						if(rds[this.name] !== undefined){
							$(rds[this.name]).trigger("change");
						}
						rds[this.name] = this;
					}
				} else {
					card.find(".card-body").addClass("d-none");
				}
			};
			card.find(".card-heading [type=\"checkbox\"]").map(refresh);
			card.find(".card-heading [type=\"checkbox\"]").change(refresh);
			card.find(".card-heading [type=\"radio\"]").map(refresh);
			card.find(".card-heading [type=\"radio\"]").change(refresh);
			return this.id;
		});
		initConfirm();
	}
	(function(oldLoad) {
		if (oldLoad == undefined) {
			window.onload = init;
		} else {
			window.onload = function() {
				init();
				oldLoad();
			}
		}
	})(window.onload);

})();
