url="http://localhost:5555"

$("#startonlinestream").click(function(){
	link=$("#onlinestream").val()
	$("#onlinestream").val("")
	$.get(url+"/_omx/play/"+escape(link))
})
function playOnTv(link){

	$.get(url+"/_omx/play"+link)
}
$("#startmagnetstream").click(function(){
	link=$("#magnetstream").val()
	// $("#magnetstream").val("")
	if(link.startsWith("magnet")){
		// link=link.substr(8)
	}else{
		link=escape(link)
	}
	
	$.get(url+"/"+link,function(data){
		
		for(i in data){
			f="<li>"+data[i].path+"<button id='torrentFile"+i+"' link='"+data[i].link+"' >play to TV</button> or <a target='_blank' href='"+data[i].link+"'>on browser</a></li>"
			
			$("#files").append(f)
			$("#torrentFile"+i).click(function(){
				tlink=$(this).attr("link")
				$.get(url+"/_omx/play"+tlink)
			})		
		}
		
	})
	console.log("get")
	// var offline=true
	// function ping(){
 //       $.ajax({
 //          url: 'http://peer.local:8000',
 //          success: function(result){
	// 		  console.log("ready",result)
	// 			offline=false
 //          },     
 //          error: function(result){
	// 		   //~ offline=true
	// 		   sleep(2000)
	// 		   ping()
 //          }
 //       });
 //    }
 //    //~ ping()
 //    function sleep(milliseconds) {
	//   var start = new Date().getTime();
	//   for (var i = 0; i < 1e7; i++) {
	//     if ((new Date().getTime() - start) > milliseconds){
	//       break;
	//     }
	//   }
	// }	
	//~ while(offline){
		//~ sleep(2000)
		//~ ping()
		//~ console.log("still sleeping")
	//~ }
	//~ console.log("ready")	
		//~ window.location = "http://peer.local:8000"	
		
})
