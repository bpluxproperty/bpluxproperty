(function(){
  var WA="393467259098", HOOK="https://services.leadconnectorhq.com/hooks/dBDJJALoNI6Gps2GwMqb/webhook-trigger/f15d46f8-6ee2-4317-93bf-14950f14fe0e";
  window.bpLead=function(e){
    e.preventDefault();
    var f=e.target, d={};
    Array.prototype.forEach.call(f.elements,function(el){if(el.name)d[el.name]=el.value;});
    d.fonte="blog "+location.pathname;
    var done=function(){f.innerHTML='<p style="font-family:Cormorant Garamond,serif;font-size:22px;color:#16140F">Grazie! Ti ricontattiamo a breve.</p>';};
    if(HOOK){
      var ok=false; try{ ok=navigator.sendBeacon(HOOK,new Blob([JSON.stringify(d)],{type:"application/json"})); }catch(e){}
      if(ok){done();} else { waFallback(d); }
    } else { waFallback(d); }
    return false;
  };
  function waFallback(d){
    var t="Ciao B&P! Richiesta dal blog.%0A"+
      "Nome: "+enc(d.nome)+"%0AEmail: "+enc(d.email||"-")+"%0ATelefono: "+enc(d.telefono||"-")+"%0ACittà: "+enc(d.citta||"-")+"%0APagina: "+enc(location.pathname);
    window.open("https://wa.me/"+WA+"?text="+t,"_blank");
  }
  function enc(s){return encodeURIComponent(s||"");}
  window.bpNews=function(e){
    e.preventDefault(); var f=e.target, em=(f.email&&f.email.value)||"";
    var d={email:em,fonte:"newsletter "+location.pathname};
    var ok=false; try{ if(HOOK) ok=navigator.sendBeacon(HOOK,new Blob([JSON.stringify(d)],{type:"application/json"})); }catch(_){}
    if(!ok && !HOOK){ window.open("https://wa.me/"+WA+"?text="+enc("Ciao B&P, iscrivimi alla newsletter: "+em),"_blank"); }
    f.innerHTML='<p style="color:#1f7a44;font-weight:500;margin:0">Iscrizione ricevuta, grazie!</p>';
    return false;
  };
})();