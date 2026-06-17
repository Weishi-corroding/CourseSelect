var TableAdvanced = function () {

    var initTable1 = function() {

        /* Formating function for row details */
        function fnFormatDetails ( tgbInfoTbl, nTr )
        {
            var aData = tgbInfoTbl.fnGetData( nTr );
            var sOut = '<span style="display:block;width:98%;text-align:center;margin-left:1%;margin-bottom:5px;font-weight:bold;">确认所选课程及班次</span>';
            if (aData['scStatus'] && '2'==aData['scStatus']) {
            	sOut += '<span style="color:red;display:block;width:98%;text-align:center;margin-left:1%;margin-bottom:5px;">您现在是二次选课，若该课程招收最大人数未满将自动录取！</span>';
            }
            if (fnColumnValue(aData,['maxCnt']) && fnColumnValue(aData,['enrollCnt']) && parseInt(fnColumnValue(aData,['maxCnt']))<=parseInt(fnColumnValue(aData,['enrollCnt']))) {
            	sOut += '<span style="display:block;width:98%;text-align:center;margin-left:1%;margin-bottom:5px;"><span style="color:red;">人数已满</span>，点击“重选”按钮重新选择班次</span>';
            } else {
            	sOut += '<span style="display:block;width:98%;text-align:center;margin-left:1%;margin-bottom:5px;">点击“确认”按钮确定选择该课程，点击“重选”按钮重新选择班次</span>';
            }
            sOut += '<table class="table_detail">';
            var sLabelTds = [];
            var sShowTds = [];
            
            sLabelTds.push('<td class="tr_detail_label" style="background-color: #4d90fe !important;padding: 4px 8px !important;">选课序号</td>');
        	sShowTds.push('<td style="background-color: #fff !important;padding: 4px 8px !important;">'+fnColumnValue(aData,['cttId'])+'</td>');
        	
        	sLabelTds.push('<td class="tr_detail_label" style="background-color: #4d90fe !important;padding: 4px 8px !important;">课程编号</td>');
        	sShowTds.push('<td style="background-color: #fff !important;padding: 4px 8px !important;">'+fnColumnValue(aData,['crCode'])+'</td>');
        	
        	sLabelTds.push('<td class="tr_detail_label" style="background-color: #4d90fe !important;padding: 4px 8px !important;">课程名称</td>');
        	sShowTds.push('<td style="background-color: #fff !important;padding: 4px 8px !important;">'+fnColumnValue(aData,['crName'])+'</td>');
        	
        	sLabelTds.push('<td class="tr_detail_label" style="background-color: #4d90fe !important;padding: 4px 8px !important;">最大录取人数</td>');
        	sShowTds.push('<td style="background-color: #fff !important;padding: 4px 8px !important;">'+fnColumnValue(aData,['maxCnt'])+'</td>');
        	
        	sLabelTds.push('<td class="tr_detail_label" style="background-color: #4d90fe !important;padding: 4px 8px !important;">已选人数</td>');
        	sShowTds.push('<td style="background-color: #fff !important;padding: 4px 8px !important;">'+fnColumnValue(aData,['applyCnt'])+'</td>');
        	
        	sLabelTds.push('<td class="tr_detail_label" style="background-color: #4d90fe !important;padding: 4px 8px !important;">已录取人数</td>');
        	sShowTds.push('<td style="background-color: #fff !important;padding: 4px 8px !important;">'+fnColumnValue(aData,['enrollCnt'])+'</td>');
        	
        	sLabelTds.push('<td class="tr_detail_label" style="background-color: #4d90fe !important;padding: 4px 8px !important;">是否选教材</td>');
        	sShowTds.push('<td style="background-color: #fff !important;padding: 3px 8px 5px !important;">'+
							'<input type="checkbox" name="buyMaterial"/>'+
						  '</td>');
        	if (fnColumnValue(aData,['onlyPrior']) && fnColumnValue(aData,['inPriorScope']) && 1==fnColumnValue(aData,['onlyPrior']) && 0==fnColumnValue(aData,['inPriorScope'])) {//已设置限制优选专业学生选课，且当前学生不在选课范围
                sLabelTds.push('<td rowspan="2" class="tr_detail_label" style="background-color: yellow !important;padding: 4px 8px !important;vertical-align:middle;color:red;font-weight:bold;">只限优选专业</td>');
            } else if (fnColumnValue(aData,['maxCnt']) && fnColumnValue(aData,['enrollCnt']) && parseInt(fnColumnValue(aData,['maxCnt']))<=parseInt(fnColumnValue(aData,['enrollCnt']))) {
        		sLabelTds.push('<td rowspan="2" class="tr_detail_label" style="background-color: yellow !important;padding: 4px 8px !important;vertical-align:middle;color:red;font-weight:bold;">已满</td>');
        	} else {
        		sLabelTds.push('<td rowspan="2" class="tr_detail_label" style="background-color: green !important;padding: 4px 8px !important;vertical-align:middle;" onclick="selectSubmit(this,'+fnColumnValue(aData,['cttId'])+')">确认</td>');
        	}
        	sLabelTds.push('<td rowspan="2" class="tr_detail_label" style="background-color: #e50112 !important;padding: 4px 8px !important;vertical-align:middle;" onclick="closeSCC(this)">重选</td>');
//            sLabelTds.push('<td rowspan="2" class="tr_detail_label" style="width:20px;background-color: #eee !important;padding: 4px 8px !important;vertical-align:middle;border:0 solid #eee !important;"><span class="saveStatus"></span></td>');
            sOut += '<tr>'+sLabelTds.join('')+'</tr><tr>'+sShowTds.join('')+'</tr>';
            sOut += '</table>';
            sOut += '<span style="color:red;display:block;width:98%;text-align:center;margin-left:1%;margin-top:5px;">注: 请学生在选每一门课程的同时，慎重选择是否需要教材，教材科将根据学生的意向统计预定教材的数量。开学购书时，教材科将优先考虑选择需要教材的同学用书，有多余的再考虑未预定教材的同学。 </span>';
             
            return sOut;
        }
        
        function fnColumnValue (aData, columnParams) {
        	var deepObj = [aData];
        	for (var i=0; i<columnParams.length; i++) {
        		deepObj.push(deepObj[i][columnParams[i]]);
        	}
        	return deepObj[columnParams.length]+'';
        }

        /*
         * Insert a 'details' column to the table
         */
        var nCloneTh = document.createElement( 'th' );
        var nCloneTd = document.createElement( 'td' );
        nCloneTd.innerHTML = '<span class="row-details row-details-close"></span>';
         
        $('#'+advancedTagId+' thead tr').each( function () {
//            this.insertBefore( nCloneTh, this.childNodes[0] );
        } );
         
        $('#'+advancedTagId+' tbody tr').each( function () {
//            this.insertBefore(  nCloneTd.cloneNode( true ), this.childNodes[0] );
        } );
         
        /* Add event listener for opening and closing details
         * Note that the indicator for showing which row is open is not controlled by DataTables,
         * rather it is done here
         */
        $('#'+advancedTagId+' .row-details').each(function(){
        	$(this).unbind('click');
        });
        $('#'+advancedTagId+' .row-details').each(function(){
        	$(this).on('click', function(){
        		var nTr = $(this).parents('tr')[0];
                if ( tgbInfoTbl.fnIsOpen(nTr) )
                {
                    /* This row is already open - close it */
                    $(this).addClass("row-details-close").removeClass("row-details-open");
                    tgbInfoTbl.fnClose( nTr );
                }
                else
                {
                    /* Open this row */                
                    $(this).addClass("row-details-open").removeClass("row-details-close");
                    tgbInfoTbl.fnOpen( nTr, fnFormatDetails(tgbInfoTbl, nTr), 'details' );
                    $('td.details').attr('colspan', $('#'+advancedTagId+' thead tr:eq(0)').children().length);
                }
        	});
        });
//        $('#'+advancedTagId).on('click', ' tbody td .row-details', function () {
//            var nTr = $(this).parents('tr')[0];
//            if ( tgbInfoTbl.fnIsOpen(nTr) )
//            {
//                /* This row is already open - close it */
//                $(this).addClass("row-details-close").removeClass("row-details-open");
//                tgbInfoTbl.fnClose( nTr );
//            }
//            else
//            {
//                /* Open this row */                
//                $(this).addClass("row-details-open").removeClass("row-details-close");
//                tgbInfoTbl.fnOpen( nTr, fnFormatDetails(tgbInfoTbl, nTr), 'details' );
//                $('td.details').attr('colspan', $('#'+advancedTagId+' thead tr:eq(0)').children().length);
//            }
//        });
    }

     var initTable2 = function() {
        $('#sample_2_column_toggler input[type="checkbox"]').change(function(){
            /* Get the DataTables object again - this is not a recreation, just a get of the object */
            var iCol = parseInt($(this).attr("data-column"));
            var bVis = tgbInfoTbl.fnSettings().aoColumns[iCol].bVisible;
            tgbInfoTbl.fnSetColumnVis(iCol, (bVis ? false : true));
        });
    }

    return {

        //main function to initiate the module
        init: function () {
            
            if (!jQuery().dataTable) {
                return;
            }

            initTable1();
            initTable2();
        }

    };

}();