(function(){
  var WA="393467259098", HOOK="";
  window.bpLead=function(e){
    e.preventDefault();
    var f=e.target, d={};
    Array.prototype.forEach.call(f.elements,function(el){if(el.name)d[el.name]=el.value;});
    d.fonte="blog "+location.pathname;
    var done=function(){f.innerHTML='<p style="font-family:Cormorant Garamond,serif;font-size:22px;color:#16140F">Grazie! Ti ricontattiamo a breve.</p>';};
    if(HOOK){
      fetch(HOOK,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})
        .then(done).catch(function(){waFallback(d);});
    } else { waFallback(d); }
    return false;
  };
  function waFallback(d){
    var t="Ciao B&P! Richiesta dal blog.%0A"+
      "Nome: "+enc(d.nome)+"%0AContatto: "+enc(d.contatto)+"%0ACitta: "+enc(d.citta||"-")+"%0APagina: "+enc(location.pathname);
    window.open("https://wa.me/"+WA+"?text="+t,"_blank");
  }
  function enc(s){return encodeURIComponent(s||"");}
})();